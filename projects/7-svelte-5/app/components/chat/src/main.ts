import "./app.css";
import App from "./App.svelte";
import { mount } from "svelte";

let app = {};
const appElement = document.getElementById("app")!;

if (appElement) {
  const chat = JSON.parse(appElement?.dataset?.chat) || {};

  let app = mount(App, {
      target: appElement,
      props: {
        initialChatState: chat,
      },
    });
}

export default app;
