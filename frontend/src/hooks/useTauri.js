import { useState, useEffect } from 'react';

/**
 * Custom hook untuk Tauri API integration
 * Detects if running in Tauri context and provides helpers
 */
export function useTauri() {
  const [isTauri, setIsTauri] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // Check if running in Tauri
    setIsTauri(window.__TAURI__ !== undefined);
  }, []);

  /**
   * Show Windows notification (when minimized to tray)
   */
  const sendNotification = async (title, body) => {
    if (!isTauri) {
      console.log('[Tauri] Not in Tauri context, skipping notification');
      return;
    }

    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('show_notification', { title, body });
      console.log('[Tauri] Notification sent:', title);
    } catch (error) {
      console.error('[Tauri] Notification error:', error);
    }
  };

  /**
   * Check if window is visible (for deciding notification vs bubble)
   */
  const checkVisibility = async () => {
    if (!isTauri) return true;

    try {
      const { appWindow } = await import('@tauri-apps/api/window');
      const visible = await appWindow.isVisible();
      setIsVisible(visible);
      return visible;
    } catch (error) {
      console.error('[Tauri] Visibility check error:', error);
      return true;
    }
  };

  /**
   * Show/hide window programmatically
   */
  const toggleWindow = async (show) => {
    if (!isTauri) return;

    try {
      const { appWindow } = await import('@tauri-apps/api/window');
      if (show) {
        await appWindow.show();
        await appWindow.setFocus();
      } else {
        await appWindow.hide();
      }
      setIsVisible(show);
    } catch (error) {
      console.error('[Tauri] Toggle window error:', error);
    }
  };

  /**
   * Minimize to tray
   */
  const minimizeToTray = () => toggleWindow(false);

  /**
   * Restore from tray
   */
  const restoreFromTray = () => toggleWindow(true);

  return {
    isTauri,
    isVisible,
    sendNotification,
    checkVisibility,
    minimizeToTray,
    restoreFromTray,
  };
}
