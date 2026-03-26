import { useEffect, useRef, useCallback, useState } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || '';

export function useWebSocket(token = null) {
  const socketRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [deviceState, setDeviceState] = useState({
    led_red: false,
    led_blue: false,
    led_green: false,
    motor: false,
    connected: false,
  });
  const [lastAction, setLastAction] = useState(null);
  const [pendingGesture, setPendingGesture] = useState(null);
  const listenersRef = useRef({});

  useEffect(() => {
    const socket = io(SOCKET_URL, {
      auth: token ? { token } : {},
      transports: ['websocket', 'polling'],
      reconnectionDelay: 1000,
      reconnectionAttempts: Infinity,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('[WS] Connected:', socket.id);
      setConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('[WS] Disconnected');
      setConnected(false);
    });

    socket.on('device:state', (state) => {
      setDeviceState(state);
    });

    socket.on('gesture:action', (action) => {
      setLastAction(action);
    });

    socket.on('gesture:pending', (state) => {
      setPendingGesture(state.pendingGesture || null);
    });

    socket.on('gesture:confirmed', (data) => {
      setLastAction(data);
      setPendingGesture(null);
    });

    return () => {
      socket.disconnect();
    };
  }, [token]);

  const sendGestureFrame = useCallback((gesture, confidence = 1.0) => {
    socketRef.current?.emit('gesture:frame', { gesture, confidence });
  }, []);

  const sendDeviceCommand = useCallback((command) => {
    socketRef.current?.emit('device:command', { command });
  }, []);

  const updateSettings = useCallback((settings) => {
    socketRef.current?.emit('settings:update', settings);
  }, []);

  return {
    connected,
    deviceState,
    lastAction,
    pendingGesture,
    sendGestureFrame,
    sendDeviceCommand,
    updateSettings,
  };
}
