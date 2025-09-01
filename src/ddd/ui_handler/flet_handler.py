from typing import Union, Optional, Any, List, Dict
import logging
import queue
import threading
import multiprocessing

import zmq

from ddd.ui_handler.handler_base import UIHandlerBase
from ddd.ui_handler.utils import ft, check_flet_available, RPCMessage, RPCResponse, RPCExecResult


# Constants
DEFAULT_RPC_PORT = 5555
DEFAULT_FLET_PORT = 5000
DEFAULT_TITLE = "DDD Toolbox"
ZMQ_TIMEOUT_MS = 5000
RPC_RESULT_TIMEOUT_SEC = 30
THREAD_JOIN_TIMEOUT_SEC = 2
THREAD_JOIN_EXTENDED_TIMEOUT_SEC = 3
POLL_TIMEOUT_MS = 100
BUSY_WAIT_SLEEP_SEC = 0.01
SCROLL_DELAY_SEC = 0.1
SCROLL_DURATION_MS = 200


# Configure logging
logger = logging.getLogger(__name__)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class FletServerProc:
    def __init__(
        self,
        rpc_port: int = DEFAULT_RPC_PORT,
        flet_port: int = DEFAULT_FLET_PORT,
        title: str = DEFAULT_TITLE,
        output_queue: queue.Queue[RPCExecResult] = None,
    ):
        check_flet_available()
        self.ft = ft

        self._should_stop = False

        # Flet components
        self.flet_port = flet_port
        self.title = title
        self.page = None
        self.content_column = None
        self.input_controls = None
        self.content_messages = []
        self.input_queue = queue.Queue()
        self.is_waiting_input = False
        self.input_config = {}
        self._is_app_running = False
        self._page_initialized = threading.Event()

        # ZMQ components
        self.context = None
        self.socket = None
        self.rpc_thread = None
        self.rpc_port = rpc_port
        self._rpc_msg_queue: queue.Queue[RPCMessage] = queue.Queue()
        self._output_queue: queue.Queue[RPCExecResult] = output_queue

        # Flet theming colors
        self.colors = {
            "primary": "#667eea",
            "secondary": "#764ba2",
            "success": "#4facfe",
            "warning": "#43e97b",
            "danger": "#f5576c",
            "info": "#38f9d7",
            "surface": "#ffffff",
            "on_surface": "#2d3748",
            "surface_variant": "#f8fafc",
            "outline": "#e2e8f0",
        }

    def __del__(self):
        """Destructor"""
        self.cleanup()

    def cleanup(self):
        """Explicitly clean up resources"""
        if hasattr(self, "_should_stop") and not self._should_stop:
            logger.info("开始清理FletServerProc资源")
            self._should_stop = True
            self._is_app_running = False

            # Close page first
            if hasattr(self, "page") and self.page:
                try:
                    self.page.window_close()
                except Exception as e:
                    logger.warning("关闭页面时出错: %s", e)
                finally:
                    self.page = None
                    self._page_initialized = threading.Event()

            # Close ZMQ resources
            if hasattr(self, "socket") and self.socket:
                try:
                    self.socket.close()
                except Exception as e:
                    logger.warning("关闭ZMQ socket时出错: %s", e)
                finally:
                    self.socket = None

            if hasattr(self, "context") and self.context:
                try:
                    self.context.term()
                except Exception as e:
                    logger.warning("终止ZMQ context时出错: %s", e)
                finally:
                    self.context = None

            # Wait for threads to finish
            if (
                hasattr(self, "rpc_thread")
                and self.rpc_thread
                and self.rpc_thread.is_alive()
            ):
                try:
                    self.rpc_thread.join(timeout=THREAD_JOIN_TIMEOUT_SEC)
                    if self.rpc_thread.is_alive():
                        logger.warning("RPC线程未能在超时时间内结束")
                except Exception as e:
                    logger.warning("等待RPC线程结束时出错: %s", e)

            # Signal completion to output queue
            if hasattr(self, "_output_queue") and self._output_queue:
                try:
                    self._output_queue.put_nowait(
                        RPCExecResult(result="cleanup_complete")
                    )
                except Exception as e:
                    logger.warning("发送清理完成信号时出错: %s", e)

            logger.info("FletServerProc资源清理完成")

    def start(self, app_config: dict):
        """Start the Flet server and RPC server"""
        logger.info("启动Flet服务器，配置: %s", app_config)
        self._start_rpc_server_thread()
        self._start_apply_rpc_method_thread()
        logger.info("RPC服务器已启动")

        # Start Flet app directly (this will block, but that's ok in the subprocess)
        try:
            logger.info("正在启动Flet应用...")
            self.ft.app(target=self._init_flet_page, **app_config)
        except Exception as e:
            logger.error("Flet应用启动失败: %s", e)
            import traceback

            traceback.print_exc()

    def _start_rpc_server_thread(self):
        """Start ZMQ RPC server"""
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{self.rpc_port}")

        self.rpc_thread = threading.Thread(target=self._rpc_loop, daemon=True)
        self.rpc_thread.start()
        logger.info("RPC server started on port %s", self.rpc_port)

    def _rpc_loop(self):
        """RPC message processing loop"""
        while not self._should_stop:
            try:
                # Use non-blocking receive with timeout
                if self.socket.poll(timeout=POLL_TIMEOUT_MS):
                    message_json = self.socket.recv_string(zmq.NOBLOCK)
                    message = RPCMessage.from_json(message_json)
                    response = self._handle_rpc(message)
                    self.socket.send_string(response.to_json())
            except zmq.Again:
                # No message available, continue
                continue
            except zmq.ContextTerminated:
                break
            except Exception as e:
                # Send error response
                error_response = RPCResponse(error=str(e))
                try:
                    self.socket.send_string(error_response.to_json())
                except Exception:
                    pass

    def _handle_rpc(self, message: RPCMessage) -> RPCResponse:
        """Handle individual RPC call"""
        try:
            method_name = message.method
            if not hasattr(self, method_name):
                return RPCResponse(
                    error=f"Method '{method_name}' not found",
                    request_id=message.request_id,
                )

            method = getattr(self, method_name)
            if not callable(method):
                return RPCResponse(
                    error=f"'{method_name}' is not callable",
                    request_id=message.request_id,
                )

            message.method = method

            # 我们不能直接在这里调用，因为1.页面可能没有初始化；2.调用阻塞函数会导致超时
            self._rpc_msg_queue.put(message)

            return RPCResponse(result="success", request_id=message.request_id)

        except Exception as e:
            return RPCResponse(error=str(e), request_id=message.request_id)

    def _start_apply_rpc_method_thread(self):
        """Start the apply RPC method thread"""
        self.apply_rpc_method_thread = threading.Thread(
            target=self._busy_apply_rpc_method, daemon=True
        )
        self.apply_rpc_method_thread.start()

    def _busy_apply_rpc_method(self):
        """Apply RPC method processing loop"""
        self._page_initialized.wait()

        while not self._should_stop:
            try:
                if not self._rpc_msg_queue.empty():
                    message = self._rpc_msg_queue.get()
                    self.apply_rpc_method(message)
                else:
                    # Short sleep to avoid busy waiting
                    import time

                    time.sleep(BUSY_WAIT_SLEEP_SEC)
            except Exception:
                # Continue processing other messages
                continue

    def apply_rpc_method(self, message: RPCMessage) -> RPCResponse:
        """Apply the RPC method"""
        method, args, kwargs = message.method, message.args, message.kwargs

        if not method:
            if self._output_queue:
                self._output_queue.put(RPCExecResult(error="方法名为空"))
            return

        if isinstance(method, str):
            try:
                method = getattr(self, method)
                if not callable(method):
                    if self._output_queue:
                        self._output_queue.put(
                            RPCExecResult(error=f"方法不可调用: {method}")
                        )
                    return
            except AttributeError:
                if self._output_queue:
                    self._output_queue.put(RPCExecResult(error=f"方法不存在: {method}"))
                return

        if not callable(method):
            if self._output_queue:
                self._output_queue.put(RPCExecResult(error=f"无效方法: {method}"))
            return

        try:
            result = method(*args, **kwargs)
            if self._output_queue:
                self._output_queue.put(RPCExecResult(result=result))
        except Exception as e:
            if self._output_queue:
                self._output_queue.put(RPCExecResult(error=str(e)))

    def destroy(self):
        """Destroy the Flet application and RPC server"""
        self.cleanup()

    def is_app_running(self):
        """Check if the Flet server is running"""
        return self._is_app_running

    def _init_flet_page(self, page):
        """Initialize the Flet page with modern UI components"""
        self.page = page
        self._setup_page_properties()

        header = self._create_header()
        content_area = self._create_content_area()
        self._create_input_area()
        self._add_welcome_message()

        # Main layout
        page.add(
            self.ft.Column(
                [
                    header,
                    self.ft.Container(content=content_area, expand=True),
                    self.input_controls,
                ],
                spacing=0,
                expand=True,
            )
        )

        self.page.update()
        logger.info("页面初始化完成，设置_page_initialized事件")
        self._page_initialized.set()

    def _setup_page_properties(self):
        """Setup basic page properties"""
        self.page.title = self.title
        self.page.theme_mode = self.ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.bgcolor = self.colors["surface_variant"]
        self.page.window_height = 800
        self.page.window_width = 1200

        # Custom theme
        self.page.theme = self.ft.Theme(
            color_scheme_seed=self.colors["primary"],
            visual_density=self.ft.VisualDensity.COMFORTABLE,
        )

    def _create_header(self):
        """Create the header component"""
        return self.ft.Container(
            content=self.ft.Row(
                [
                    self.ft.Icon(
                        self.ft.Icons.ROCKET_LAUNCH, color=self.ft.Colors.WHITE, size=32
                    ),
                    self.ft.Column(
                        [
                            self.ft.Text(
                                self.title,
                                size=28,
                                weight=self.ft.FontWeight.BOLD,
                                color=self.ft.Colors.WHITE,
                            ),
                            self.ft.Text(
                                "现代化交互式工具箱",
                                size=14,
                                color=self.ft.Colors.WHITE70,
                            ),
                        ],
                        spacing=2,
                    ),
                ],
                alignment=self.ft.MainAxisAlignment.CENTER,
            ),
            gradient=self.ft.LinearGradient(
                [
                    self.ft.Colors.with_opacity(0.8, self.colors["primary"]),
                    self.ft.Colors.with_opacity(0.8, self.colors["secondary"]),
                ]
            ),
            padding=self.ft.padding.all(20),
            margin=self.ft.margin.all(0),
        )

    def _create_content_area(self):
        """Create the main content area"""
        self.content_column = self.ft.Column(
            scroll=self.ft.ScrollMode.AUTO, spacing=10, expand=True
        )

        return self.ft.Container(
            content=self.content_column,
            bgcolor=self.ft.Colors.WHITE,
            border_radius=16,
            padding=self.ft.padding.all(20),
            margin=self.ft.margin.all(20),
            shadow=self.ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=self.ft.Colors.with_opacity(0.1, self.ft.Colors.BLACK),
                offset=self.ft.Offset(0, 4),
            ),
        )

    def _create_input_area(self):
        """Create the input area (initially hidden)"""
        self.input_controls = self.ft.Container(
            visible=False,
            bgcolor=self.ft.Colors.WHITE,
            border_radius=16,
            padding=self.ft.padding.all(20),
            margin=self.ft.margin.only(left=20, right=20, bottom=20),
            shadow=self.ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=self.ft.Colors.with_opacity(0.2, self.ft.Colors.BLACK),
                offset=self.ft.Offset(0, 8),
            ),
        )

    def _add_welcome_message(self):
        """Add welcome message to content area"""
        welcome_card = self.ft.Card(
            content=self.ft.Container(
                content=self.ft.Row(
                    [
                        self.ft.Icon(
                            self.ft.Icons.INFO, color=self.colors["info"], size=24
                        ),
                        self.ft.Column(
                            [
                                self.ft.Text(
                                    "欢迎使用 DDD 工具箱！",
                                    size=16,
                                    weight=self.ft.FontWeight.BOLD,
                                    color=self.colors["on_surface"],
                                ),
                                self.ft.Text(
                                    "这是一个现代化的 Flet Web 界面，提供原生组件交互体验。",
                                    size=14,
                                    color=self.ft.Colors.GREY_700,
                                ),
                            ],
                            expand=True,
                            spacing=5,
                        ),
                    ]
                ),
                padding=self.ft.padding.all(20),
                bgcolor=self.ft.Colors.LIGHT_BLUE_50,
                border=self.ft.border.all(1, self.ft.Colors.LIGHT_BLUE_200),
                border_radius=12,
            ),
            elevation=2,
        )
        self.content_column.controls.append(welcome_card)

    def clear_screen(self):
        """Clear the content display"""
        if self.content_column:
            self.content_column.controls.clear()
            self.content_messages.clear()
            if self.page:
                self.page.update()

    def print_text(
        self, text: Union[str, Any] = "", style: Optional[str] = None, end: str = "\n"
    ):
        """Print text using Flet Text component"""
        if not self.content_column:
            return

        # Convert Text objects to string
        if hasattr(text, "plain"):
            text = text.plain
        elif not isinstance(text, str):
            text = str(text)

        if not text.strip() and end == "\n":
            return  # Skip empty lines

        # Determine text style and color
        text_color = self.colors["on_surface"]
        text_weight = self.ft.FontWeight.NORMAL
        text_size = 14

        if style:
            if "primary" in style or "cyan" in style:
                text_color = self.colors["primary"]
                text_weight = self.ft.FontWeight.W_500
            elif "success" in style or "green" in style:
                text_color = self.colors["success"]
            elif "warning" in style or "yellow" in style:
                text_color = self.colors["warning"]
            elif "danger" in style or "red" in style:
                text_color = self.colors["danger"]
            elif "bold" in style:
                text_weight = self.ft.FontWeight.BOLD

        text_widget = self.ft.Text(
            text,
            size=text_size,
            weight=text_weight,
            color=text_color,
            font_family="monospace",
        )

        text_container = self.ft.Container(
            content=text_widget,
            padding=self.ft.padding.symmetric(vertical=2, horizontal=8),
            margin=self.ft.margin.symmetric(vertical=1),
        )

        self.content_column.controls.append(text_container)
        self._update_page()

    def print_panel(
        self,
        content: Union[str, Any],
        title: Optional[str] = None,
        style: Optional[str] = None,
        border_style: Optional[str] = None,
        box_type: Optional[str] = None,
        padding: tuple = (0, 1),
        title_align: str = "left",
    ) -> None:
        """Print content in a modern Flet Card component"""
        if not self.content_column:
            return

        # Handle content types
        if hasattr(content, "renderable"):
            content = content.renderable
        if hasattr(content, "plain"):
            content = content.plain
        elif not isinstance(content, str):
            content = str(content)

        # Determine card styling based on style parameter
        card_bgcolor = self.ft.Colors.LIGHT_BLUE_50
        border_color = self.ft.Colors.LIGHT_BLUE_200
        icon_name = self.ft.Icons.INFO
        icon_color = self.colors["info"]

        if style:
            if "green" in style or "success" in style:
                card_bgcolor = self.ft.Colors.GREEN_50
                border_color = self.ft.Colors.GREEN_200
                icon_name = self.ft.Icons.CHECK_CIRCLE
                icon_color = self.colors["success"]
            elif "red" in style or "danger" in style or "error" in style:
                card_bgcolor = self.ft.Colors.RED_50
                border_color = self.ft.Colors.RED_200
                icon_name = self.ft.Icons.ERROR
                icon_color = self.colors["danger"]
            elif "yellow" in style or "warning" in style:
                card_bgcolor = self.ft.Colors.ORANGE_50
                border_color = self.ft.Colors.ORANGE_200
                icon_name = self.ft.Icons.WARNING
                icon_color = self.colors["warning"]

        # Create panel content
        panel_content = self.ft.Row(
            [
                self.ft.Icon(icon_name, color=icon_color, size=24),
                self.ft.Column(
                    [
                        self.ft.Text(
                            title if title else "信息",
                            size=16,
                            weight=self.ft.FontWeight.BOLD,
                            color=self.colors["on_surface"],
                        )
                        if title
                        else None,
                        self.ft.Text(
                            content,
                            size=14,
                            color=self.ft.Colors.GREY_700,
                            selectable=True,
                        ),
                    ],
                    expand=True,
                    spacing=5,
                ),
            ]
        )

        # Remove None elements
        if not title:
            panel_content.controls[1].controls = panel_content.controls[1].controls[1:]

        panel_card = self.ft.Card(
            content=self.ft.Container(
                content=panel_content,
                padding=self.ft.padding.all(20),
                bgcolor=card_bgcolor,
                border=self.ft.border.all(1, border_color),
                border_radius=12,
            ),
            elevation=2,
            margin=self.ft.margin.symmetric(vertical=5),
        )

        self.content_column.controls.append(panel_card)
        self._update_page()

    def print_table(
        self,
        title: Optional[str] = None,
        title_style: Optional[str] = None,
        columns: Optional[List[Dict[str, Any]]] = None,
        rows: Optional[List[List[str]]] = None,
        **kwargs,
    ) -> None:
        """Create and print a modern Flet DataTable"""
        if not self.content_column:
            return

        # Create DataTable columns
        data_columns = []
        if columns:
            for col in columns:
                header = col.get("header", col.get("name", ""))
                data_columns.append(
                    self.ft.DataColumn(
                        label=self.ft.Text(
                            header,
                            weight=self.ft.FontWeight.BOLD,
                            color=self.ft.Colors.WHITE,
                        )
                    )
                )

        # Create DataTable rows
        data_rows = []
        if rows:
            for row in rows:
                cells = []
                for cell in row:
                    cells.append(
                        self.ft.DataCell(
                            self.ft.Text(
                                str(cell), size=13, color=self.colors["on_surface"]
                            )
                        )
                    )
                data_rows.append(self.ft.DataRow(cells=cells))

        # Create DataTable
        data_table = self.ft.DataTable(
            columns=data_columns,
            rows=data_rows,
            bgcolor=self.ft.Colors.WHITE,
            border_radius=12,
            heading_row_color=self.ft.Colors.with_opacity(0.8, self.colors["primary"]),
            heading_row_height=60,
            column_spacing=20,
        )

        # Wrap in container with title
        table_container = self.ft.Column(
            [
                self.ft.Container(
                    content=self.ft.Row(
                        [
                            self.ft.Icon(
                                self.ft.Icons.TABLE_CHART,
                                color=self.colors["primary"],
                                size=24,
                            ),
                            self.ft.Text(
                                title if title else "数据表格",
                                size=18,
                                weight=self.ft.FontWeight.BOLD,
                                color=self.colors["on_surface"],
                            ),
                        ]
                    ),
                    padding=self.ft.padding.all(10),
                )
                if title
                else None,
                self.ft.Container(
                    content=data_table,
                    border_radius=12,
                    shadow=self.ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=5,
                        color=self.ft.Colors.with_opacity(0.1, self.ft.Colors.BLACK),
                        offset=self.ft.Offset(0, 2),
                    ),
                ),
            ],
            spacing=10,
        )

        # Remove None elements
        if not title:
            table_container.controls = table_container.controls[1:]

        table_card = self.ft.Card(
            content=self.ft.Container(
                content=table_container, padding=self.ft.padding.all(20)
            ),
            elevation=3,
            margin=self.ft.margin.symmetric(vertical=10),
        )

        self.content_column.controls.append(table_card)
        self._update_page()

    def get_input(
        self, prompt: Union[str, Any] = "", default: str = ""
    ) -> Optional[str]:
        """Get user input through modern Flet components"""
        if hasattr(prompt, "plain"):
            prompt = prompt.plain

        if not self.input_controls or not self.page:
            return default

        prompt_lower = prompt.lower()

        # Create input UI based on prompt type
        if any(word in prompt_lower for word in ["y/n", "yes/no", "是否", "确认"]):
            result = self._create_yes_no_input(prompt)
        elif any(
            word in prompt_lower for word in ["继续", "continue", "proceed", "下一步"]
        ):
            result = self._create_continue_input(prompt, default)
        elif any(
            word in prompt_lower
            for word in ["选择", "choose", "select", "菜单", "menu"]
        ):
            result = self._create_menu_input(prompt)
        else:
            result = self._create_text_input(prompt, default)

        return result

    def _create_yes_no_input(self, prompt: str) -> Optional[str]:
        """Create Yes/No button input"""

        def on_yes_click(e):
            self.input_queue.put("y")
            self._hide_input_area()

        def on_no_click(e):
            self.input_queue.put("n")
            self._hide_input_area()

        buttons_row = self.ft.Row(
            [
                self._create_styled_button(
                    "是 (Yes)",
                    self.ft.Icons.CHECK,
                    self.colors["success"],
                    on_yes_click,
                ),
                self._create_styled_button(
                    "否 (No)", self.ft.Icons.CLOSE, self.ft.Colors.GREY_400, on_no_click
                ),
            ],
            spacing=20,
            alignment=self.ft.MainAxisAlignment.CENTER,
        )

        self.input_controls.content = self._create_input_ui_base(
            prompt, self.ft.Icons.HELP, [buttons_row]
        )
        self._show_input_area()
        return self._wait_for_input()

    def _create_continue_input(self, prompt: str, default: str) -> Optional[str]:
        """Create Continue button input"""

        def on_continue_click(e):
            self.input_queue.put(default or "continue")
            self._hide_input_area()

        def on_cancel_click(e):
            self.input_queue.put("cancel")
            self._hide_input_area()

        buttons_row = self.ft.Row(
            [
                self._create_styled_button(
                    "继续",
                    self.ft.Icons.ARROW_FORWARD,
                    self.colors["primary"],
                    on_continue_click,
                ),
                self._create_styled_button(
                    "取消",
                    self.ft.Icons.CANCEL,
                    self.ft.Colors.GREY_400,
                    on_cancel_click,
                ),
            ],
            spacing=20,
            alignment=self.ft.MainAxisAlignment.CENTER,
        )

        self.input_controls.content = self._create_input_ui_base(
            prompt, self.ft.Icons.PLAY_ARROW, [buttons_row]
        )
        self._show_input_area()
        return self._wait_for_input()

    def _create_menu_input(self, prompt: str) -> Optional[str]:
        """Create menu selection input"""

        def on_option1_click(e):
            self.input_queue.put("1")
            self._hide_input_area()

        def on_option2_click(e):
            self.input_queue.put("2")
            self._hide_input_area()

        def on_back_click(e):
            self.input_queue.put("back")
            self._hide_input_area()

        buttons_row = self.ft.Row(
            [
                self._create_styled_button(
                    "选项 1",
                    self.ft.Icons.LOOKS_ONE,
                    self.colors["primary"],
                    on_option1_click,
                ),
                self._create_styled_button(
                    "选项 2",
                    self.ft.Icons.LOOKS_TWO,
                    self.colors["primary"],
                    on_option2_click,
                ),
                self._create_styled_button(
                    "返回",
                    self.ft.Icons.ARROW_BACK,
                    self.ft.Colors.GREY_400,
                    on_back_click,
                ),
            ],
            spacing=15,
            alignment=self.ft.MainAxisAlignment.CENTER,
        )

        self.input_controls.content = self._create_input_ui_base(
            prompt, self.ft.Icons.LIST, [buttons_row]
        )
        self._show_input_area()
        return self._wait_for_input()

    def _create_text_input(self, prompt: str, default: str) -> Optional[str]:
        """Create text input field"""
        text_field = self.ft.TextField(
            label=prompt,
            value=default,
            border_radius=12,
            bgcolor=self.ft.Colors.WHITE,
            border_color=self.colors["outline"],
            focused_border_color=self.colors["primary"],
            expand=True,
        )

        def on_submit_click(e):
            value = text_field.value or default
            self.input_queue.put(value)
            self._hide_input_area()

        text_field.on_submit = on_submit_click

        input_row = self.ft.Row(
            [
                text_field,
                self._create_styled_button(
                    "确认", self.ft.Icons.CHECK, self.colors["primary"], on_submit_click
                ),
            ],
            spacing=15,
        )

        self.input_controls.content = self._create_input_ui_base(
            prompt, self.ft.Icons.EDIT, [input_row]
        )
        self._show_input_area()

        # Auto-focus the text field
        text_field.focus()
        self.page.update()

        return self._wait_for_input()

    def _show_input_area(self):
        """Show the input area"""
        if self.input_controls:
            self.input_controls.visible = True
            self.is_waiting_input = True
            self.page.update()

    def _hide_input_area(self):
        """Hide the input area"""
        if self.input_controls:
            self.input_controls.visible = False
            self.is_waiting_input = False
            self.page.update()

    def _wait_for_input(self) -> Optional[str]:
        """Wait for user input and return the result"""
        while self.is_waiting_input:
            try:
                user_input = self.input_queue.get(timeout=BUSY_WAIT_SLEEP_SEC * 10)

                # Display the input in content area
                self._add_input_response(user_input)

                return user_input

            except queue.Empty:
                continue
            except KeyboardInterrupt:
                self.is_waiting_input = False
                self._hide_input_area()
                return None

        return None

    def _add_input_response(self, user_input: str):
        """Add user input response to content area"""
        response_card = self.ft.Card(
            content=self.ft.Container(
                content=self.ft.Row(
                    [
                        self.ft.Icon(
                            self.ft.Icons.PERSON, color=self.colors["primary"], size=24
                        ),
                        self.ft.Column(
                            [
                                self.ft.Text(
                                    "用户输入",
                                    size=14,
                                    weight=self.ft.FontWeight.BOLD,
                                    color=self.colors["on_surface"],
                                ),
                                self.ft.Text(
                                    f"❯ {user_input}",
                                    size=14,
                                    color=self.ft.Colors.GREY_700,
                                    selectable=True,
                                ),
                            ],
                            expand=True,
                            spacing=5,
                        ),
                    ]
                ),
                padding=self.ft.padding.all(15),
                bgcolor=self.ft.Colors.PURPLE_50,
                border=self.ft.border.all(1, self.ft.Colors.PURPLE_200),
                border_radius=12,
            ),
            elevation=1,
            margin=self.ft.margin.symmetric(vertical=5),
        )

        self.content_column.controls.append(response_card)
        self._update_page()

    def _update_page(self):
        """Update the page and scroll to bottom"""
        if self.page:
            self.page.update()
            # Auto-scroll to bottom
            if self.content_column:
                import time

                # Small delay to ensure content is rendered
                threading.Timer(
                    SCROLL_DELAY_SEC, lambda: self._scroll_to_bottom()
                ).start()

    def _scroll_to_bottom(self):
        """Scroll content to bottom"""
        if self.page and self.content_column:
            try:
                self.content_column.scroll_to(
                    offset=-1,  # Scroll to end
                    duration=SCROLL_DURATION_MS,
                )
                self.page.update()
            except Exception:
                pass  # Ignore scroll errors

    def create_choice_input(
        self, prompt: str, choices: List[Dict[str, str]]
    ) -> Optional[str]:
        """Create a custom choice input with specified buttons

        Args:
            prompt: The prompt text
            choices: List of choice dictionaries with keys: text, value, style (optional), icon (optional)
        """
        buttons = []

        def create_button_handler(choice_value):
            def handler(e):
                self.input_queue.put(choice_value)
                self._hide_input_area()

            return handler

        for choice in choices:
            # Map style to colors
            btn_bgcolor = self.colors["primary"]
            if choice.get("style") == "btn-success":
                btn_bgcolor = self.colors["success"]
            elif choice.get("style") == "btn-warning":
                btn_bgcolor = self.colors["warning"]
            elif choice.get("style") == "btn-danger":
                btn_bgcolor = self.colors["danger"]
            elif choice.get("style") == "btn-secondary":
                btn_bgcolor = self.ft.Colors.GREY_400

            # Extract icon from HTML if present
            icon_widget = None
            if choice.get("icon"):
                icon_html = choice["icon"]
                if "fa-check" in icon_html:
                    icon_widget = self.ft.Icons.CHECK
                elif "fa-times" in icon_html:
                    icon_widget = self.ft.Icons.CLOSE
                elif "fa-arrow-right" in icon_html:
                    icon_widget = self.ft.Icons.ARROW_FORWARD
                elif "fa-arrow-left" in icon_html:
                    icon_widget = self.ft.Icons.ARROW_BACK
                else:
                    icon_widget = self.ft.Icons.TOUCH_APP

            button = self.ft.ElevatedButton(
                text=choice["text"],
                icon=icon_widget,
                bgcolor=btn_bgcolor,
                color=self.ft.Colors.WHITE,
                on_click=create_button_handler(choice["value"]),
                style=self.ft.ButtonStyle(
                    shape=self.ft.RoundedRectangleBorder(radius=12)
                ),
            )
            buttons.append(button)

        self.input_controls.content = self.ft.Column(
            [
                self.ft.Row(
                    [
                        self.ft.Icon(
                            self.ft.Icons.MOUSE, color=self.colors["primary"], size=24
                        ),
                        self.ft.Text(
                            prompt,
                            size=16,
                            weight=self.ft.FontWeight.W_500,
                            color=self.colors["on_surface"],
                            expand=True,
                        ),
                    ]
                ),
                self.ft.Row(
                    buttons,
                    spacing=15,
                    alignment=self.ft.MainAxisAlignment.CENTER,
                    wrap=True,
                ),
            ],
            spacing=20,
        )

        self._show_input_area()

        user_input = self._wait_for_input()

        # Find choice text for display
        choice_text = user_input
        for choice in choices:
            if choice["value"] == user_input:
                choice_text = choice["text"]
                break

        return user_input

    def _create_input_ui_base(self, prompt: str, icon: str, controls: list):
        """Create base input UI structure with common prompt and icon"""
        return self.ft.Column(
            [
                self.ft.Row(
                    [
                        self.ft.Icon(icon, color=self.colors["primary"], size=24),
                        self.ft.Text(
                            prompt,
                            size=16,
                            weight=self.ft.FontWeight.W_500,
                            color=self.colors["on_surface"],
                            expand=True,
                        ),
                    ]
                ),
                *controls,  # Unpack the controls list
            ],
            spacing=20,
        )

    def _create_styled_button(
        self, text: str, icon: str, bgcolor: str, on_click_handler
    ):
        """Create a styled button with consistent appearance"""
        return self.ft.ElevatedButton(
            text=text,
            icon=icon,
            bgcolor=bgcolor,
            color=self.ft.Colors.WHITE,
            on_click=on_click_handler,
            style=self.ft.ButtonStyle(shape=self.ft.RoundedRectangleBorder(radius=12)),
        )


class FletUIHandler(UIHandlerBase):
    """Modern Web-based GUI handler using Flet with ZMQ RPC communication"""

    def __init__(
        self,
        flet_port: int = DEFAULT_FLET_PORT,
        rpc_port: int = DEFAULT_RPC_PORT,
        title: str = DEFAULT_TITLE,
    ):
        self.flet_port = flet_port
        self.rpc_port = rpc_port
        self.title = title
        self._cleanup_done = False

        # Initialize attributes to None for safe cleanup
        self.context = None
        self.socket = None
        self.server_proc = None
        self._output_queue = None

        try:
            # Create output queue for async results
            self._output_queue: queue.Queue[RPCExecResult] = multiprocessing.Queue()

            # ZMQ client setup
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.REQ)
            self.socket.connect(f"tcp://localhost:{self.rpc_port}")
            self.socket.setsockopt(zmq.RCVTIMEO, ZMQ_TIMEOUT_MS)
            self.socket.setsockopt(zmq.SNDTIMEO, ZMQ_TIMEOUT_MS)

            # Start Flet server process
            self._start_flet_process()

            logger.info("正在启动 Flet Web 应用...")
            logger.info("Flet应用将在端口 %s 运行", self.flet_port)
            logger.info("RPC通信将在端口 %s 运行", self.rpc_port)
            logger.info("请在浏览器中访问 http://127.0.0.1:%s", self.flet_port)

        except Exception as e:
            logger.error("初始化FletUIHandler失败: %s", e)
            self.cleanup()  # Clean up partial initialization
            raise

    def _start_flet_process(self):
        """Start the Flet server process"""

        def run_flet_server(output_queue: queue.Queue[RPCExecResult]):
            check_flet_available()
            logger.info("Flet导入成功")

            server = FletServerProc(
                rpc_port=self.rpc_port,
                flet_port=self.flet_port,
                title=self.title,
                output_queue=output_queue,
            )
            logger.info("FletServerProc实例创建成功")

            app_config = {
                "view": ft.AppView.WEB_BROWSER,
                "host": "127.0.0.1",
                "port": self.flet_port,
            }
            logger.info("应用配置: %s", app_config)

            server.start(app_config)
            logger.info("Flet服务器启动完成")

        self.server_proc = multiprocessing.Process(
            target=run_flet_server, args=(self._output_queue,)
        )
        self.server_proc.start()

        # Wait for server to start
        # time.sleep(2)

    def rpc(self, method: str, *args, **kwargs) -> Any:
        """Send RPC request to the Flet server process"""
        if self._cleanup_done:
            raise RuntimeError("UIHandler已被清理，无法执行RPC调用")

        if not self.socket or not self._output_queue:
            raise RuntimeError("RPC组件未正确初始化")

        try:
            message = RPCMessage(method=method, args=list(args), kwargs=kwargs)
            self.socket.send_string(message.to_json())

            # Get RPC confirmation response
            response_json = self.socket.recv_string()
            response = RPCResponse.from_json(response_json)

        except zmq.Again:
            raise TimeoutError(f"RPC call to '{method}' timed out")
        except Exception as e:
            raise RuntimeError(f"RPC call failed: {e}")

        if response.error:
            raise RuntimeError(f"RPC error: {response.error}")

        # Get the result from the output queue
        try:
            exec_res = self._output_queue.get(timeout=RPC_RESULT_TIMEOUT_SEC)
            if exec_res.error:
                raise RuntimeError(f"RPC method execution error: {exec_res.error}")
            return exec_res.result
        except queue.Empty:
            raise TimeoutError(f"Waiting for result of '{method}' timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to get RPC result: {e}")

    def clear_screen(self):
        """Clear screen via RPC"""
        return self.rpc("clear_screen")

    def print_text(
        self, text: Union[str, Any] = "", style: Optional[str] = None, end: str = "\n"
    ):
        """Print text via RPC"""
        # Convert Text objects to string for JSON serialization
        if hasattr(text, "plain"):
            text = text.plain
        elif not isinstance(text, str):
            text = str(text)
        return self.rpc("print_text", text, style=style, end=end)

    def print_panel(
        self,
        content: Union[str, Any],
        title: Optional[str] = None,
        style: Optional[str] = None,
        border_style: Optional[str] = None,
        box_type: Optional[str] = None,
        padding: tuple = (0, 1),
        title_align: str = "left",
    ) -> None:
        """Print panel via RPC"""
        # Convert content to string for JSON serialization
        if hasattr(content, "plain"):
            content = content.plain
        elif not isinstance(content, str):
            content = str(content)
        return self.rpc(
            "print_panel",
            content,
            title=title,
            style=style,
            border_style=border_style,
            padding=padding,
            title_align=title_align,
        )

    def print_table(
        self,
        title: Optional[str] = None,
        title_style: Optional[str] = None,
        columns: Optional[List[Dict[str, Any]]] = None,
        rows: Optional[List[List[str]]] = None,
        box_type: Optional[str] = None,
        border_style: Optional[str] = None,
        show_header: bool = True,
        **kwargs,
    ) -> None:
        """Create and print table via RPC"""
        # Call RPC
        self.rpc(
            "print_table",
            title=title,
            title_style=title_style,
            columns=columns,
            rows=rows,
            **kwargs,
        )

    def get_input(
        self, prompt: Union[str, Any] = "", default: str = ""
    ) -> Optional[str]:
        """Get user input via RPC"""
        if hasattr(prompt, "plain"):
            prompt = prompt.plain
        elif not isinstance(prompt, str):
            prompt = str(prompt)
        return self.rpc("get_input", prompt, default=default)

    def create_choice_input(
        self, prompt: str, choices: List[Dict[str, str]]
    ) -> Optional[str]:
        """Create choice input via RPC"""
        return self.rpc("create_choice_input", prompt, choices)

    def force_page_initialization(self) -> bool:
        """Force page initialization for testing purposes"""
        try:
            result = self.rpc("force_page_initialization")
            return result
        except Exception as e:
            logger.error("强制初始化失败: %s", e)
            return False

    def __del__(self):
        """Destructor to clean up resources"""
        self.cleanup()

    def cleanup(self):
        """Explicitly clean up resources"""
        if hasattr(self, "_cleanup_done") and self._cleanup_done:
            return

        logger.info("开始清理FletUIHandler资源")

        # Signal server to cleanup
        try:
            self.rpc("destroy")
        except Exception as e:
            logger.warning("发送destroy信号失败: %s", e)

        # Terminate server process
        if hasattr(self, "server_proc") and self.server_proc:
            try:
                if self.server_proc.is_alive():
                    self.server_proc.terminate()
                    self.server_proc.join(timeout=THREAD_JOIN_EXTENDED_TIMEOUT_SEC)
                    if self.server_proc.is_alive():
                        logger.warning("服务器进程未响应terminate，使用kill")
                        self.server_proc.kill()
                        self.server_proc.join(timeout=1)
            except Exception as e:
                logger.warning("终止服务器进程时出错: %s", e)

        # Close ZMQ resources
        if hasattr(self, "socket") and self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.warning("关闭ZMQ socket时出错: %s", e)
            finally:
                self.socket = None

        if hasattr(self, "context") and self.context:
            try:
                self.context.term()
            except Exception as e:
                logger.warning("终止ZMQ context时出错: %s", e)
            finally:
                self.context = None

        # Clean up output queue
        if hasattr(self, "_output_queue") and self._output_queue:
            try:
                # Clear any remaining items in the queue
                while not self._output_queue.empty():
                    try:
                        self._output_queue.get_nowait()
                    except:
                        break
                self._output_queue.close()
            except Exception as e:
                logger.warning("清理输出队列时出错: %s", e)
            finally:
                self._output_queue = None

        self._cleanup_done = True
        logger.info("FletUIHandler资源清理完成")
