from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QPushButton
except Exception:  # pragma: no cover
    QAction = None
    QPushButton = None


def _latest_markdown_from_main_window(main_window: Any) -> Path | None:
    candidates: list[Any] = [
        getattr(main_window, "output_markdown", None),
        getattr(main_window, "last_markdown_path", None),
        getattr(main_window, "_last_markdown_path", None),
    ]

    payload = getattr(main_window, "_last_payload", None) or getattr(main_window, "last_payload", None)
    if isinstance(payload, dict):
        candidates.extend(
            [
                payload.get("output_markdown"),
                payload.get("markdown_path"),
                payload.get("output_markdown_path"),
            ]
        )

        for item in payload.get("output_files", []) or []:
            candidates.append(item)

    for candidate in candidates:
        if not candidate:
            continue
        path = Path(str(candidate))
        if path.suffix.lower() in {".md", ".markdown", ".txt"} and path.exists():
            return path

    return None


def _default_output_dir_for_markdown(path: Path | None) -> Path | None:
    if path is None:
        return None
    return path.parent / f"{path.stem}_rendered"


def _open_markdown_render_dialog(parent: Any) -> None:
    from chapterfold_app.gui.markdown_render_dialog import MarkdownRenderDialog

    md = _latest_markdown_from_main_window(parent)
    dialog = MarkdownRenderDialog(
        parent,
        initial_markdown_path=md,
        initial_output_dir=_default_output_dir_for_markdown(md),
    )
    dialog.exec()


def _find_or_create_menu(main_window: Any, title: str):
    menu_bar = main_window.menuBar()

    if not hasattr(main_window, "_chapterfold_extra_menus"):
        main_window._chapterfold_extra_menus = {}

    key = title.replace("&", "")
    existing = main_window._chapterfold_extra_menus.get(key)
    if existing is not None:
        try:
            existing.actions()
            return existing
        except RuntimeError:
            main_window._chapterfold_extra_menus.pop(key, None)

    for action in menu_bar.actions():
        try:
            menu = action.menu()
            if menu is not None and menu.title().replace("&", "") == key:
                main_window._chapterfold_extra_menus[key] = menu
                return menu
        except RuntimeError:
            continue

    menu = menu_bar.addMenu(title)
    main_window._chapterfold_extra_menus[key] = menu
    return menu


def install_markdown_render_action(main_window: Any) -> bool:
    if QAction is None or not hasattr(main_window, "menuBar"):
        return False

    if getattr(main_window, "_chapterfold_markdown_render_action_installed", False):
        return True

    tools_menu = _find_or_create_menu(main_window, "&Tools")
    action_text = "Render Edited Markdown..."

    for action in tools_menu.actions():
        try:
            if action.text().replace("&", "") == action_text:
                main_window._chapterfold_markdown_render_action = action
                main_window._chapterfold_markdown_render_menu = tools_menu
                main_window._chapterfold_markdown_render_action_installed = True
                return True
        except RuntimeError:
            continue

    action = QAction(action_text, main_window)
    action.triggered.connect(lambda checked=False: _open_markdown_render_dialog(main_window))
    tools_menu.addAction(action)

    main_window._chapterfold_markdown_render_action = action
    main_window._chapterfold_markdown_render_menu = tools_menu
    main_window._chapterfold_markdown_render_action_installed = True
    return True


def install_markdown_render_button(main_window: Any) -> bool:
    if QPushButton is None:
        return False

    if getattr(main_window, "_chapterfold_markdown_render_button_installed", False):
        return True

    try:
        existing_buttons = main_window.findChildren(QPushButton)
    except Exception:
        existing_buttons = []

    for button in existing_buttons:
        try:
            if button.text().replace("&", "") == "Render Edited Markdown":
                main_window._chapterfold_markdown_render_button = button
                main_window._chapterfold_markdown_render_button_installed = True
                return True
        except RuntimeError:
            continue

    anchor = None
    for button in existing_buttons:
        try:
            label = button.text().replace("&", "")
        except RuntimeError:
            continue
        if label in {"Open Markdown", "Open Markdown File"}:
            anchor = button
            break

    if anchor is None:
        return False

    parent = anchor.parentWidget()
    layout = parent.layout() if parent is not None else None
    if layout is None:
        return False

    new_button = QPushButton("Render Edited Markdown", parent)
    new_button.setToolTip("Render an edited ChapterFOLD Markdown file back into PDF/DOCX outputs.")
    new_button.clicked.connect(lambda checked=False: _open_markdown_render_dialog(main_window))

    inserted = False
    try:
        for idx in range(layout.count()):
            item = layout.itemAt(idx)
            widget = item.widget() if item is not None else None
            if widget is anchor:
                layout.insertWidget(idx + 1, new_button)
                inserted = True
                break
    except Exception:
        inserted = False

    if not inserted:
        try:
            layout.addWidget(new_button)
        except Exception:
            return False

    main_window._chapterfold_markdown_render_button = new_button
    main_window._chapterfold_markdown_render_button_installed = True
    return True


def install_markdown_render_ui(main_window: Any) -> bool:
    menu_ok = install_markdown_render_action(main_window)
    button_ok = install_markdown_render_button(main_window)
    return bool(menu_ok or button_ok)
