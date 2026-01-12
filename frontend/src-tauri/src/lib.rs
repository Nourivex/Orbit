use tauri::{Manager, WindowEvent};
use tauri_plugin_notification::NotificationExt;

#[tauri::command]
async fn show_notification(app: tauri::AppHandle, title: String, body: String) -> Result<(), String> {
    app.notification()
        .builder()
        .title(title)
        .body(body)
        .show()
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_window_state::Builder::default().build())
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                // Minimize to system tray instead of closing
                window.hide().unwrap();
                api.prevent_close();
            }
        })
        .invoke_handler(tauri::generate_handler![show_notification])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            // Position window to bottom-right on startup
            let window = app.get_webview_window("main").unwrap();
            
            // Get primary monitor
            if let Ok(Some(monitor)) = window.primary_monitor() {
                let size = monitor.size();
                let window_size = window.outer_size().unwrap();
                
                // Bottom-right with 20px margin
                let x = size.width as i32 - window_size.width as i32 - 20;
                let y = size.height as i32 - window_size.height as i32 - 60;
                
                window.set_position(tauri::Position::Physical(tauri::PhysicalPosition {
                    x,
                    y,
                })).ok();
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
