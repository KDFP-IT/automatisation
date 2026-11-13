'use strict';

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('officeChat', {
  state: () => ipcRenderer.invoke('chat:state'),
  subscribe: listener => { ipcRenderer.on('chat:update', (_, state) => listener(state)); },
  send: message => ipcRenderer.invoke('chat:send', message),
  setStatus: status => ipcRenderer.invoke('chat:status', status),
  quit: () => ipcRenderer.invoke('chat:quit'),
});
