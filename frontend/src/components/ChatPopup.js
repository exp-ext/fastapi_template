import React, { useState, useEffect, useRef } from 'react';
import './ChatPopup.css';

const ChatPopup = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const socket = useRef(null);
  const messageEndRef = useRef(null);
  const roomName = useRef(createUUID());

  const token = localStorage.getItem('token');

  const scrollToBottom = () => {
    if (messageEndRef.current) {
      messageEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    const wsUrl = `ws://${window.location.host}/ws/${roomName.current}?token=${token}`;
    socket.current = new WebSocket(wsUrl);

    socket.current.onopen = () => {
      if (token) {
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

    socket.current.onclose = () => {
      console.log('WebSocket connection closed');
    };

    return () => {
      socket.current.close();
    };
  }, [token]);

  const sendMessage = () => {
    if (inputMessage.trim() !== '') {
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
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  const handleInputChange = (e) => {
    setInputMessage(e.target.value);
  };

  return (
    <div className={`chat-popup ${isOpen ? 'open' : ''}`}>
      <div className="chat-header" onClick={toggleChat}>
        <h4>Чат</h4>
        <button className="close-chat">{isOpen ? 'Закрыть' : 'Открыть'}</button>
      </div>
      {isOpen && (
        <div className="chat-content">
          <ul className="messages">
            {messages.map((msg, index) => (
              <li key={index} className={`message ${msg.type}`}>
                <div dangerouslySetInnerHTML={{ __html: msg.content }} />
              </li>
            ))}
            <div ref={messageEndRef} />
          </ul>
          <div className="chat-footer">
            <input
              type="text"
              value={inputMessage}
              onChange={handleInputChange}
              placeholder="Введите сообщение"
              className="message-input"
            />
            <button onClick={sendMessage} className="send-message">
              Отправить
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

function createUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    return ((Math.random() * 16) | 0).toString(16);
  });
}

export default ChatPopup;
