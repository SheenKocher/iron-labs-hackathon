import { useState, useRef, useEffect, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { CHAT } from "@/constants/testIds";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import ReactMarkdown from "react-markdown";
import {
  Send,
  Mail,
  UserSearch,
  FileText,
  Users,
  Sparkles,
  ExternalLink,
  ArrowRight,
  Zap,
  Brain,
  Wrench,
  FolderOpen,
  BarChart3,
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const QUICK_ACTIONS = [
  { label: "Draft cold email", icon: Mail, prompt: "Draft a cold email to Jordan Lee at Acme Corp about our sales automation platform" },
  { label: "Review an email", icon: FileText, prompt: "Review this email: Hi Jordan, I noticed your team is growing fast. We help teams like yours close 30% more deals with AI-powered outreach. Want to grab 15 mins this week?" },
  { label: "Look up prospect", icon: UserSearch, prompt: "Look up prospect Sarah Chen" },
  { label: "Check deal", icon: BarChart3, prompt: "Check deal D-1042" },
  { label: "Find leads", icon: Users, prompt: "Find similar leads in the SaaS industry" },
];

function MetadataBadges({ metadata }) {
  if (!metadata) return null;
  return (
    <div className="flex flex-wrap gap-2 mb-4" data-testid={CHAT.metadataBadge}>
      <span className="badge-model inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] sm:text-xs font-mono uppercase tracking-[0.1em] rounded-sm">
        <Brain className="w-3 h-3" />
        {metadata.model_used}
      </span>
      <span className="badge-tool inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] sm:text-xs font-mono uppercase tracking-[0.1em] rounded-sm">
        <Wrench className="w-3 h-3" />
        {metadata.tool_used}
      </span>
      <span className="badge-category inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] sm:text-xs font-mono uppercase tracking-[0.1em] rounded-sm">
        <FolderOpen className="w-3 h-3" />
        {metadata.category}
      </span>
    </div>
  );
}

function EmailDraftCard({ emailDraft }) {
  if (!emailDraft) return null;

  const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=&su=${encodeURIComponent(emailDraft.subject)}&body=${encodeURIComponent(emailDraft.body)}`;

  return (
    <div className="email-card rounded-sm p-4 sm:p-5 mt-4" data-testid="email-draft-card">
      <div className="flex items-center gap-2 mb-3">
        <Mail className="w-4 h-4 text-zinc-400" />
        <span className="font-mono text-[10px] sm:text-xs uppercase tracking-[0.1em] text-zinc-500">Email Draft</span>
      </div>
      <div className="mb-2">
        <span className="text-xs text-zinc-500 font-mono uppercase tracking-wider">Subject</span>
        <p className="text-sm text-white mt-1">{emailDraft.subject}</p>
      </div>
      <Separator className="my-3 bg-white/10" />
      <div className="mb-4">
        <span className="text-xs text-zinc-500 font-mono uppercase tracking-wider">Body</span>
        <p className="text-sm text-zinc-300 mt-1 whitespace-pre-wrap leading-relaxed">{emailDraft.body}</p>
      </div>
      <a
        href={gmailUrl}
        target="_blank"
        rel="noopener noreferrer"
        data-testid={CHAT.sendGmailButton}
        className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-sm border border-red-500/20 text-red-400 hover:bg-red-500/10 transition-all duration-200"
      >
        <ExternalLink className="w-3.5 h-3.5" />
        Send via Gmail
      </a>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 py-8" data-testid={CHAT.typingIndicator}>
      <span className="font-mono text-xs text-zinc-500 tracking-wider">
        PitchRoute is synthesizing
      </span>
      <span className="w-2 h-4 bg-amber-400/80 animate-blink" />
    </div>
  );
}

function UserMessage({ content }) {
  return (
    <div className="max-w-[80%]" data-testid={CHAT.userMessage}>
      <p className="font-heading text-xl sm:text-2xl lg:text-3xl font-light tracking-tight text-white leading-snug">
        {content}
      </p>
    </div>
  );
}

function AIResponse({ content, metadata, emailDraft }) {
  return (
    <div className="animate-slide-up" data-testid={CHAT.aiResponse}>
      <MetadataBadges metadata={metadata} />
      <div className="ai-response-content text-sm sm:text-base leading-relaxed text-zinc-300">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
      <EmailDraftCard emailDraft={emailDraft} />
    </div>
  );
}

function EmptyState({ onQuickAction }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4" data-testid={CHAT.emptyState}>
      <div className="mb-8">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-sm bg-amber-400/10 border border-amber-400/20 mb-6">
          <Zap className="w-6 h-6 text-amber-400" />
        </div>
        <h1 className="font-heading text-3xl sm:text-4xl lg:text-5xl font-light tracking-tight text-white mb-3">
          PitchRoute
        </h1>
        <p className="text-sm sm:text-base text-zinc-500 max-w-md">
          AI-powered sales assistant. Draft emails, review pitches, research prospects, and find leads.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-2xl w-full">
        {QUICK_ACTIONS.map((action, idx) => (
          <button
            key={idx}
            onClick={() => onQuickAction(action.prompt)}
            data-testid={`${CHAT.quickActionChip}-${idx}`}
            className="quick-chip flex items-center gap-3 px-4 py-3 rounded-sm text-left text-sm transition-all duration-200 hover:border-white/30"
          >
            <action.icon className="w-4 h-4 flex-shrink-0" />
            <span>{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  const sendMessage = async (text) => {
    const userMsg = text || input.trim();
    if (!userMsg || isLoading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setIsLoading(true);

    try {
      const { data } = await axios.post(`${API}/chat`, { message: userMsg });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          metadata: data.metadata,
          emailDraft: data.email_draft,
        },
      ]);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || "Something went wrong";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${errorMsg}`,
          metadata: { model_used: "N/A", tool_used: "none", category: "error", complexity: "N/A" },
        },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleQuickAction = (prompt) => {
    sendMessage(prompt);
  };

  return (
    <div className="h-screen flex flex-col bg-[#09090B]">
      {/* Header */}
      <header className="flex items-center gap-3 px-4 sm:px-8 py-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-sm bg-amber-400/10 border border-amber-400/20 flex items-center justify-center">
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <span className="font-heading text-sm font-medium tracking-tight text-white">PitchRoute</span>
        </div>
        <Separator orientation="vertical" className="h-5 bg-white/10" />
        <span className="font-mono text-[10px] text-zinc-600 uppercase tracking-[0.15em]">AI Sales Assistant</span>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-hidden" data-testid={CHAT.thread}>
        <div
          ref={scrollRef}
          className="h-full overflow-y-auto"
          data-testid={CHAT.messageList}
        >
          <div className="max-w-4xl mx-auto w-full px-4 sm:px-8 pb-48 pt-8">
            {messages.length === 0 && !isLoading ? (
              <EmptyState onQuickAction={handleQuickAction} />
            ) : (
              <div className="space-y-10 sm:space-y-14">
                {messages.map((msg, idx) => (
                  <div key={idx}>
                    {msg.role === "user" ? (
                      <UserMessage content={msg.content} />
                    ) : (
                      <AIResponse
                        content={msg.content}
                        metadata={msg.metadata}
                        emailDraft={msg.emailDraft}
                      />
                    )}
                  </div>
                ))}
                {isLoading && <TypingIndicator />}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Input Bar */}
      <div className="input-bar-glass border-t border-white/[0.06] p-4 sm:p-6" data-testid={CHAT.inputBar}>
        <div className="max-w-4xl mx-auto w-full">
          {/* Quick actions above input when conversation started */}
          {messages.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {QUICK_ACTIONS.slice(0, 3).map((action, idx) => (
                <button
                  key={idx}
                  onClick={() => handleQuickAction(action.prompt)}
                  data-testid={`${CHAT.quickActionChip}-inline-${idx}`}
                  className="quick-chip inline-flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs"
                  disabled={isLoading}
                >
                  <action.icon className="w-3 h-3" />
                  {action.label}
                </button>
              ))}
            </div>
          )}

          {/* Input container */}
          <div className="input-container-focus flex items-center gap-2 bg-[#121214] border border-white/[0.08] rounded-sm px-4 py-2.5">
            <Sparkles className="w-4 h-4 text-zinc-600 flex-shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask PitchRoute anything..."
              className="flex-1 bg-transparent border-none outline-none text-sm text-white placeholder:text-zinc-600 font-body"
              disabled={isLoading}
              data-testid={CHAT.inputField}
            />
            <Button
              size="icon"
              variant="ghost"
              onClick={() => sendMessage()}
              disabled={!input.trim() || isLoading}
              data-testid={CHAT.sendButton}
              className="h-8 w-8 text-zinc-500 hover:text-amber-400 hover:bg-amber-400/10 rounded-sm transition-all duration-200 disabled:opacity-30"
            >
              {isLoading ? (
                <ArrowRight className="w-4 h-4 animate-pulse" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>

          <p className="font-mono text-[10px] text-zinc-700 mt-2 text-center tracking-wider">
            POWERED BY IRONLABS ROUTING ENGINE
          </p>
        </div>
      </div>
    </div>
  );
}
