import {
  createContext,
  createElement,
  useContext,
  useState,
  type ReactNode,
} from "react";

export interface ViewAsUser {
  id: number;
  name: string | null;
  picture: string | null;
}

interface ViewAsContextValue {
  viewAsUser: ViewAsUser | null;
  setViewAsUser: (user: ViewAsUser | null) => void;
}

const ViewAsContext = createContext<ViewAsContextValue | null>(null);

export function ViewAsProvider({ children }: { children: ReactNode }) {
  const [viewAsUser, setViewAsUser] = useState<ViewAsUser | null>(null);

  return createElement(
    ViewAsContext.Provider,
    { value: { viewAsUser, setViewAsUser } },
    children,
  );
}

export function useViewAs(): ViewAsContextValue {
  const context = useContext(ViewAsContext);
  if (!context) {
    throw new Error("useViewAs must be used within a ViewAsProvider");
  }
  return context;
}
