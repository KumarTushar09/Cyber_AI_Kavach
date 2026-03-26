// URL-only mode: keep the full workspace import commented for later phases.
// import { ChatWorkspace } from "../components/workspace/chat_workspace";
import { UrlWorkspace } from "../components/workspace/url_workspace";

export default function HomePage() {
  // return <ChatWorkspace initialPanel="overview" />;
  return <UrlWorkspace />;
}
