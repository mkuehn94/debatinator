// Minimal always-on-top overlay. All logic lives in live/server.py; the UI just listens to its SSE stream.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, WindowEvent};

fn main() {
    // WebKitGTK + NVIDIA: DMA-BUF renderer fails ("Failed to create GBM buffer") → blank window
    #[cfg(target_os = "linux")]
    if std::env::var_os("WEBKIT_DISABLE_DMABUF_RENDERER").is_none() {
        std::env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1");
    }
    tauri::Builder::default()
        .setup(|app| {
            let win = app.get_webview_window("main").expect("main window");
            win.set_always_on_top(true)?;
            let w = win.clone();
            // some WMs drop "keep above" after focus changes / fullscreen apps → re-assert
            win.on_window_event(move |e| {
                if let WindowEvent::Focused(false) = e {
                    let _ = w.set_always_on_top(true);
                }
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri app");
}
