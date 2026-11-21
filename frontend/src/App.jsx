
import { useState } from 'react'
import './App.css'

function App() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const handleSend = async (e) => {
    e?.preventDefault()

    const trimmedQuestion = question.trim()

    if (!trimmedQuestion || loading) return

    setMessages((previous) => [
      ...previous,
      { type: 'user', text: trimmedQuestion },
    ])

    setQuestion('')
    setLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: trimmedQuestion,
        }),
      })

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`)
      }

      const data = await response.json()

      setMessages((previous) => [
        ...previous,
        {
          type: 'assistant',
          text: data.answer,
          sources: data.sources || [],
        },
      ])
    } catch (error) {
      console.error('Chat error:', error)

      setMessages((previous) => [
        ...previous,
        {
          type: 'assistant',
          text: 'Unable to connect to CampusGPT. Please check whether the backend and Ollama are running.',
          sources: [],
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">C</div>
          <h2>CampusGPT</h2>
        </div>

        <button
          className="new-chat"
          onClick={() => setMessages([])}
        >
          + New Chat
        </button>

        <div className="sidebar-info">
          <h4>ABOUT</h4>
          <p>Your AI-powered college information assistant.</p>
        </div>

        <div className="sidebar-footer">
          <span>Powered by Local AI</span>
          <span>Mistral + RAG</span>
        </div>
      </aside>

      <main className="chat-area">
        <header className="topbar">
          <div>
            <h3>CT University Assistant</h3>
            <p>College Information Chatbot</p>
          </div>

          <div className="status">
            <span className="status-dot"></span>
            Online
          </div>
        </header>

        <section className="chat-content">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-icon">🎓</div>

              <h1>Welcome to CampusGPT</h1>

              <p>
                Your college information assistant.
                Ask me anything about academic calendars,
                examinations, holidays and university information.
              </p>

              <div className="suggestions">
                <button
                  onClick={() =>
                    setQuestion('When do end-semester examinations begin?')
                  }
                >
                  📅 Examination dates
                </button>

                <button
                  onClick={() =>
                    setQuestion('When do winter vacations begin?')
                  }
                >
                  ❄️ Winter vacations
                </button>

                <button
                  onClick={() =>
                    setQuestion('When do next semester classes begin?')
                  }
                >
                  📚 Next semester
                </button>
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`message ${message.type}`}
                >
                  <div className="message-avatar">
                    {message.type === 'user' ? 'You' : 'C'}
                  </div>

                  <div className="message-body">
                    <div className="message-text">
                      {message.text}
                    </div>

                    {message.type === 'assistant' &&
                      message.sources?.length > 0 && (
                        <div className="sources">
                          <strong>Sources:</strong>

                          {message.sources.map((source, sourceIndex) => (
                            <div key={sourceIndex} className="source-item">
                              {source.source_type === 'website' ? (
                                <>
                                  🌐{' '}
                                  <a
                                    href={source.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                  >
                                    {source.title || source.document}
                                  </a>
                                </>
                              ) : (
                                <>
                                  📄 {source.document}
                                  {source.page != null &&
                                    ` — Page ${source.page}`}
                                </>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message assistant">
                  <div className="message-avatar">C</div>
                  <div className="message-text">
                    CampusGPT is thinking...
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        <div className="input-container">
          <form className="chat-input" onSubmit={handleSend}>
            <input
              type="text"
              placeholder="Ask anything about your university..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
            />

            <button type="submit" disabled={!question.trim() || loading}>
              {loading ? 'Wait...' : 'Send ↑'}
            </button>
          </form>

          <p className="input-note">
            CampusGPT answers using information from available college documents and university webpages.
          </p>
        </div>
      </main>
    </div>
  )
}

export default App
