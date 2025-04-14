import { create } from "zustand";
import { persist } from "zustand/middleware";

interface TodoistSettings {
  defaultProjectId: string | null;
}

export const defaultSettings: TodoistSettings = {
  defaultProjectId: null,
};

interface TodoistSettingsStore {
  settings: TodoistSettings;
  saveSettings: (state: TodoistSettings) => void;
}

export const useTodoistSettingsStore = create<TodoistSettingsStore>()(
  persist(
    (set) => ({
      settings: defaultSettings,
      saveSettings: (state: TodoistSettings) => {
        set({
          settings: state,
        });
      },
    }),
    {
      name: "todoist-settings",
    }
  )
);
