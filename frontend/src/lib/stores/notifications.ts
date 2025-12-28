import { writable, derived } from "svelte/store";

export type NotificationType = "success" | "error" | "warning" | "info";
export type NotificationPosition =
  | "top-right"
  | "top-left"
  | "bottom-right"
  | "bottom-left"
  | "top-center"
  | "bottom-center";

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
  persistent?: boolean;
  actions?: NotificationAction[];
  icon?: string;
  timestamp: Date;
  progress?: number;
  metadata?: any;
}

export interface NotificationAction {
  label: string;
  action: () => void;
  style?: "primary" | "secondary" | "danger";
}

export interface NotificationConfig {
  position: NotificationPosition;
  maxNotifications: number;
  defaultDuration: number;
  enableSound: boolean;
  enableDesktopNotifications: boolean;
}

// Default configuration
const defaultConfig: NotificationConfig = {
  position: "top-right",
  maxNotifications: 5,
  defaultDuration: 5000,
  enableSound: true,
  enableDesktopNotifications: true,
};

// Stores
export const notifications = writable<Notification[]>([]);
export const notificationConfig = writable<NotificationConfig>(defaultConfig);

// Derived store for active notifications
export const activeNotifications = derived(
  [notifications, notificationConfig],
  ([$notifications, $config]) => {
    return $notifications.slice(0, $config.maxNotifications);
  },
);

// Sound effects
const sounds = {
  success: "/sounds/success.mp3",
  error: "/sounds/error.mp3",
  warning: "/sounds/warning.mp3",
  info: "/sounds/info.mp3",
};

// Helper to play notification sound
async function playSound(type: NotificationType) {
  const config = get<NotificationConfig>(notificationConfig);
  if (!config.enableSound) return;

  try {
    const audio = new Audio(sounds[type]);
    audio.volume = 0.5;
    await audio.play();
  } catch {
    // Silent failure
  }
}

// Helper to show desktop notification
async function showDesktopNotification(notification: Notification) {
  const config = get<NotificationConfig>(notificationConfig);
  if (!config.enableDesktopNotifications) return;

  if ("Notification" in window && Notification.permission === "granted") {
    try {
      const desktopNotif = new Notification(notification.title, {
        body: notification.message,
        icon: notification.icon || "/favicon.png",
        tag: notification.id,
        requireInteraction: notification.persistent,
      });

      if (!notification.persistent && notification.duration) {
        setTimeout(() => desktopNotif.close(), notification.duration);
      }

      desktopNotif.onclick = () => {
        window.focus();
        desktopNotif.close();
      };
    } catch {
      // Silent failure
    }
  }
}

// Main notification functions
export function addNotification(
  type: NotificationType,
  title: string,
  message?: string,
  options?: Partial<Notification>,
): string {
  const config = get<NotificationConfig>(notificationConfig);
  const id = crypto.randomUUID();

  const notification: Notification = {
    id,
    type,
    title,
    message,
    duration: options?.duration ?? config.defaultDuration,
    persistent: options?.persistent ?? false,
    actions: options?.actions,
    icon: options?.icon,
    timestamp: new Date(),
    progress: options?.progress,
    metadata: options?.metadata,
  };

  notifications.update((n) => [notification, ...n]);

  // Play sound and show desktop notification
  playSound(type);
  showDesktopNotification(notification);

  // Auto-remove non-persistent notifications
  if (!notification.persistent && notification.duration) {
    setTimeout(() => {
      removeNotification(id);
    }, notification.duration);
  }

  return id;
}

export function removeNotification(id: string) {
  notifications.update((n) => n.filter((notif) => notif.id !== id));
}

export function clearAllNotifications() {
  notifications.set([]);
}

export function updateNotification(id: string, updates: Partial<Notification>) {
  notifications.update((n) =>
    n.map((notif) => (notif.id === id ? { ...notif, ...updates } : notif)),
  );
}

// Convenience functions
export const notify = {
  success: (title: string, message?: string, options?: Partial<Notification>) =>
    addNotification("success", title, message, options),

  error: (title: string, message?: string, options?: Partial<Notification>) =>
    addNotification("error", title, message, { ...options, persistent: true }),

  warning: (title: string, message?: string, options?: Partial<Notification>) =>
    addNotification("warning", title, message, options),

  info: (title: string, message?: string, options?: Partial<Notification>) =>
    addNotification("info", title, message, options),

  loading: (title: string, message?: string) => {
    return addNotification("info", title, message, {
      persistent: true,
      icon: "⏳",
    });
  },

  progress: (id: string, progress: number, message?: string) => {
    updateNotification(id, { progress, message });
  },
};

// Request desktop notification permission
export async function requestNotificationPermission() {
  if ("Notification" in window && Notification.permission === "default") {
    const permission = await Notification.requestPermission();
    return permission === "granted";
  }
  return false;
}

// WebSocket notification handler
export function handleWebSocketNotification(data: any) {
  const { type, title, message, ...options } = data;

  switch (data.event) {
    case "agent_response":
      notify.info(`🤖 ${data.agentName}`, data.message);
      break;

    case "task_completed":
      notify.success("Task Completed", data.taskName, {
        icon: "✅",
      });
      break;

    case "error":
      notify.error("Error", data.error, {
        persistent: true,
      });
      break;

    case "connection_status":
      if (data.connected) {
        notify.success("Connected", "WebSocket connection established");
      } else {
        notify.warning("Disconnected", "WebSocket connection lost");
      }
      break;

    default:
      if (type && title) {
        addNotification(type, title, message, options);
      }
  }
}

// Utility to get store value
function get<T>(store: any): T {
  let value!: T;
  store.subscribe((v: T) => (value = v))();
  return value;
}
