'use client';

import React, {
  useState,
  useEffect,
  useRef,
  ChangeEvent,
  KeyboardEvent,
} from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { FaComments, FaPaperPlane } from 'react-icons/fa';
import '../styles/ChatPopup.css';

interface Message {
  content: string;
  type: 'self' | 'other';
  isStream: boolean;
  isStreaming?: boolean;
}

const ChatPopup: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const socket = useRef<WebSocket | null>(null);
  const messageEndRef = useRef<HTMLDivElement | null>(null);
  const roomName = useRef<string>(createUUID());
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const token =
    typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const scrollToBottom = () => {
    if (messageEndRef.current) {
      messageEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = `ws://dev.yourtodo.ru/ws/${roomName.current}?token=${token}`;
      socket.current = new WebSocket(wsUrl);

      socket.current.onopen = () => {
        console.log('WebSocket connection established');
        if (token && socket.current?.readyState === WebSocket.OPEN) {
          socket.current.send(JSON.stringify({ token }));
        }
      };

      socket.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const isStreaming = data.is_stream || false;

        if (isStreaming) {
          if (data.is_start) {
            setMessages((prevMessages) => [
              ...prevMessages,
              {
                content: data.message,
                type: data.username === 'GPT' ? 'other' : 'self',
                isStream: true,
                isStreaming: true,
              },
            ]);
          } else {
            setMessages((prevMessages) => {
              const lastMessage = prevMessages[prevMessages.length - 1];

              if (
                lastMessage &&
                lastMessage.isStream &&
                lastMessage.isStreaming
              ) {
                const updatedMessage = {
                  ...lastMessage,
                  content:
                    data.message !== '' ? data.message : lastMessage.content,
                  isStreaming: !data.is_end,
                };
                return [...prevMessages.slice(0, -1), updatedMessage];
              }
              return prevMessages;
            });
          }
        } else {
          setMessages((prevMessages) => [
            ...prevMessages,
            {
              content: data.message,
              type: data.username === 'GPT' ? 'other' : 'self',
              isStream: false,
            },
          ]);
        }

        scrollToBottom();
      };

      socket.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      socket.current.onclose = () => {
        console.log('WebSocket connection closed. Reconnecting...');
        setTimeout(connectWebSocket, 5000); // Переподключение через 5 секунд
      };
    };

    connectWebSocket();

    return () => {
      socket.current?.close();
    };
  }, [token]);

  const sendMessage = () => {
    if (inputMessage.trim() !== '' && socket.current) {
      if (socket.current.readyState === WebSocket.OPEN) {
        const messageData = { text: inputMessage };

        setMessages((prevMessages) => [
          ...prevMessages,
          {
            content: inputMessage,
            type: 'self',
            isStream: false,
          },
        ]);

        socket.current.send(JSON.stringify(messageData));
        setInputMessage('');
        scrollToBottom();

        if (inputRef.current) {
          inputRef.current.style.height = '40px';
        }
      } else if (socket.current.readyState === WebSocket.CONNECTING) {
        console.warn('WebSocket is still connecting. Retrying in 500ms...');
        setTimeout(() => sendMessage(), 500);
      } else {
        console.error('WebSocket is not ready to send messages.');
      }
    }
  };

  const toggleChat = () => {
    setIsOpen((prev) => !prev);
  };

  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);

    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className={`chat-popup ${isOpen ? 'open' : 'closed'}`}>
      <div className="chat-header" onClick={toggleChat}>
        {isOpen ? <h4>Чат</h4> : <FaComments className="chat-icon" />}
      </div>
      {isOpen && (
        <div className="chat-content">
          <ul className="messages">
            {messages.map((msg, index) => (
              <li key={index} className={`message ${msg.type}`}>
                <div
                  dangerouslySetInnerHTML={{
                    __html: sanitizeContent(msg.content),
                  }}
                />
              </li>
            ))}
            <div ref={messageEndRef} />
          </ul>
          <div className="chat-footer">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Введите сообщение"
              className="message-input"
              rows={1}
            />
            <button onClick={sendMessage} className="send-message">
              <FaPaperPlane />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Функция для безопасной обработки HTML-содержимого
const sanitizeContent = (content: string): string => {
  const rawHtml = marked(content);
  return DOMPurify.sanitize(rawHtml);
};

// Генератор уникального идентификатора
function createUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export default ChatPopup;
