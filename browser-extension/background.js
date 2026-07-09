const API = "http://localhost:8000";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "research-selection",
    title: 'Research "%s" with Research Agent',
    contexts: ["selection"],
  });
  chrome.contextMenus.create({
    id: "research-page",
    title: "Research this page's topic",
    contexts: ["page"],
  });
});

async function runResearch(topic) {
  await chrome.storage.local.set({
    status: "loading",
    topic,
    data: null,
    error: null,
  });

  try {
    const res = await fetch(API + "/run/" + encodeURIComponent(topic));
    const json = await res.json();

    if (json.error) {
      await chrome.storage.local.set({ status: "error", error: json.error, topic, data: null });
    } else if (json.message) {
      await chrome.storage.local.set({ status: "error", error: json.message, topic, data: null });
    } else {
      await chrome.storage.local.set({ status: "done", data: json.data, topic, error: null });
    }
  } catch (err) {
    await chrome.storage.local.set({
      status: "error",
      error: "Couldn't reach the backend. Make sure it's running at " + API + ".",
      topic,
      data: null,
    });
  }

  // pop the extension's own action icon badge to signal results are ready
  chrome.action.setBadgeText({ text: "1" });
  chrome.action.setBadgeBackgroundColor({ color: "#6B8FE0" });
}

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "research-selection" && info.selectionText) {
    runResearch(info.selectionText.trim());
  } else if (info.menuItemId === "research-page" && tab?.title) {
    runResearch(tab.title.trim());
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.action === "search" && message.topic) {
    runResearch(message.topic.trim());
  }
});

chrome.action.onClicked.addListener(() => {
  chrome.action.setBadgeText({ text: "" });
});
