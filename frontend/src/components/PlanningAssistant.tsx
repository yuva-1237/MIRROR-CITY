import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, MapPin } from 'lucide-react';

interface SuggestedAction {
  type: string;
  name: string;
}

interface Message {
  sender: 'user' | 'assistant';
  text: string;
  suggestedAction?: SuggestedAction | null;
}

interface PlanningAssistantProps {
  scenarioId: number | null;
  authToken: string;
  onDeploySuggestedTool: (type: string) => void;
}

export default function PlanningAssistant({
  scenarioId,
  authToken,
  onDeploySuggestedTool
}: PlanningAssistantProps) {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'assistant',
      text: "🤖 **Welcome to Mirror City AI Planning Assistant!**\n\nAsk me about infrastructure trade-offs, flood vulnerability, or optimized placement, for example:\n- *'What happens if rainfall increases by 40%?'*\n- *'Where is the best place for a hospital?'*\n- *'Should we widen the downtown roads?'*"
    }
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    const userText = prompt;
    setPrompt('');
    setMessages(prev => [...prev, { sender: 'user', text: userText }]);
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/simulations/assistant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          prompt: userText,
          scenario_id: scenarioId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to reach assistant');
      }

      const data = await response.json();
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: data.reply,
        suggestedAction: data.suggested_action
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: "⚠️ **System Communication Error**: Unable to establish contact with the AI coordinator. Please check if the FastAPI server is running."
      }]);
    } finally {
      setLoading(false);
    }
  };

  const formatMessageText = (text: string) => {
    // Simple formatter for bolding, warning emojis, lists
    return text.split('\n').map((line, i) => {
      let formatted = line;
      // Bold formatter
      const boldRegex = /\*\*(.*?)\*\*/g;
      const parts = [];
      let lastIdx = 0;
      let match;

      while ((match = boldRegex.exec(line)) !== null) {
        if (match.index > lastIdx) {
          parts.push(line.substring(lastIdx, match.index));
        }
        parts.push(<strong key={match.index} className="text-white font-semibold">{match[1]}</strong>);
        lastIdx = boldRegex.lastIndex;
      }
      if (lastIdx < line.length) {
        parts.push(line.substring(lastIdx));
      }

      const elementLine = parts.length > 0 ? <>{parts}</> : formatted;

      if (line.startsWith('- ') || line.startsWith('* ')) {
        return <li key={i} className="ml-4 list-disc text-slate-300 text-xs mt-1">{parts.length > 0 ? parts : line.substring(2)}</li>;
      }
      return <p key={i} className="text-xs leading-5 mt-1">{elementLine}</p>;
    });
  };

  return (
    <div className="flex flex-col h-full bg-[#101625]/60 border border-brand-border rounded-2xl overflow-hidden glass-panel">
      {/* Header */}
      <div className="px-4 py-3 border-b border-brand-border bg-brand-panel flex items-center gap-2">
        <Sparkles size={16} className="text-brand-neonCyan" />
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
          AI Planning Assistant
        </h3>
      </div>

      {/* Messages Box */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex flex-col max-w-[90%] ${
              msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'
            }`}
          >
            <div
              className={`p-3 rounded-2xl text-xs ${
                msg.sender === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-none'
                  : 'bg-[#1a233d] border border-brand-border text-slate-300 rounded-tl-none'
              }`}
            >
              {formatMessageText(msg.text)}
            </div>

            {/* Render Suggestion Action Button */}
            {msg.suggestedAction && (
              <button
                onClick={() => onDeploySuggestedTool(msg.suggestedAction!.type)}
                className="mt-2 flex items-center gap-1.5 px-3 py-1.5 bg-brand-neonCyan/20 text-brand-neonCyan border border-brand-neonCyan/40 hover:bg-brand-neonCyan/35 text-[10px] font-bold rounded-lg transition-all animate-bounce"
              >
                <MapPin size={10} />
                Deploy: {msg.suggestedAction.name}
              </button>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-slate-500 italic px-2">
            <div className="w-1.5 h-1.5 bg-brand-neonCyan rounded-full animate-ping"></div>
            AI System is running multi-agent checks...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-3 border-t border-brand-border bg-[#0d1220]/80">
        <div className="relative">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={loading}
            placeholder="Ask a planning question..."
            className="w-full bg-[#101625] border border-brand-border rounded-xl py-2.5 pl-3 pr-10 text-xs text-gray-200 placeholder-slate-500 focus:outline-none focus:border-brand-neonCyan transition-all"
          />
          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-lg transition-all"
          >
            <Send size={12} />
          </button>
        </div>
      </form>
    </div>
  );
}
