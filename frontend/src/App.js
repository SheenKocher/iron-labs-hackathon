import { useState, useRef, useEffect, useCallback } from "react";
import "@/App.css";
import { CHAT } from "@/constants/testIds";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
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
  ChevronRight,
  CheckCircle2,
  Database,
  Search,
  PenLine,
  Copy,
  Check,
  PanelRightOpen,
  PanelRightClose,
  CircleDot,
  Loader2,
  AlertCircle,
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const QUICK_ACTIONS = [
  { label: "Draft cold email", icon: Mail, prompt: "Draft a cold email to Jordan Lee at Acme Corp about our sales automation platform" },
  { label: "Review an email", icon: FileText, prompt: "Review this email: Hi Jordan, I noticed your team is growing fast. We help teams like yours close 30% more deals with AI-powered outreach. Want to grab 15 mins this week?" },
  { label: "Look up prospect", icon: UserSearch, prompt: "Look up prospect Sarah Chen" },
  { label: "Check deal", icon: BarChart3, prompt: "Check deal D-1042" },
  { label: "Find leads", icon: Users, prompt: "Find similar leads in the SaaS industry" },
];

const TOOL_ICONS = {
  generate_cold_email: PenLine,
  review_email: FileText,
  lookup_prospect: UserSearch,
  get_deal_notes: Database,
  find_similar_leads: Search,
  none: CircleDot,
};

const TOOL_LABELS = {
  generate_cold_email: "Generate Cold Email",
  review_email: "Review Email",
  lookup_prospect: "Lookup Prospect",
  get_deal_notes: "Get Deal Notes",
  find_similar_leads: "Find Similar Leads",
  none: "General Response",
};

const CATEGORY_LABELS = {
  cold_email_draft: "Cold Email Draft",
  email_review: "Email Review",
  prospect_lookup: "Prospect Lookup",
  deal_lookup: "Deal Lookup",
  lead_gen: "Lead Generation",
  general: "General",
};

function MetadataBadges({ metadata }) {
  if (!metadata) return null;
  const tools = metadata.tool_used?.split(" → ") || ["none"];
  const categories = metadata.category?.split(" → ") || ["general"];
  const isMultiStep = tools.length > 1;

  return (
    <div className="flex flex-wrap gap-2 mb-4" data-testid={CHAT.metadataBadge}>
      <span className="badge-model inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] sm:text-xs font-mono uppercase tracking-[0.1em] rounded-sm">
        <Brain className="w-3 h-3" />
        {metadata.model_used}
      </span>
      <span className="badge-tool inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] sm:text-xs font-mono uppercase tracking-[0.1em] rounded-sm">
        <Wrench className="w-3 h-3" />
        {isMultiStep ? `${tools.length} STEPS` : tools[0]?.toUpperCase()}
      </span>
      <span className="badge-category inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] sm:text-xs font-mono uppercase tracking-[0.1em] rounded-sm">
        <FolderOpen className="w-3 h-3" />
        {categories[categories.length - 1]?.toUpperCase()}
      </span>
    </div>
  );
}

function EmailDraftCard({ emailDraft }) {
  const [copied, setCopied] = useState(false);
  if (!emailDraft) return null;

  const handleSendGmail = () => {
    const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=&su=${encodeURIComponent(emailDraft.subject)}&body=${encodeURIComponent(emailDraft.body)}`;
    navigator.clipboard.writeText(gmailUrl).catch(() => {});
    try {
      (window.top || window).open(gmailUrl, "_blank");
    } catch (e) {
      window.location.href = `mailto:?subject=${encodeURIComponent(emailDraft.subject)}&body=${encodeURIComponent(emailDraft.body)}`;
    }
  };

  const handleMailto = () => {
    window.location.href = `mailto:?subject=${encodeURIComponent(emailDraft.subject)}&body=${encodeURIComponent(emailDraft.body)}`;
  };

  const handleCopyDraft = () => {
    navigator.clipboard.writeText(`Subject: ${emailDraft.subject}\n\n${emailDraft.body}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

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
      <div className="flex flex-wrap gap-2">
        <button onClick={handleSendGmail} data-testid={CHAT.sendGmailButton}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-sm border border-red-500/20 text-red-400 hover:bg-red-500/10 transition-all duration-200">
          <ExternalLink className="w-3.5 h-3.5" /> Open in Gmail
        </button>
        <button onClick={handleMailto} data-testid="mailto-button"
          className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-sm border border-white/10 text-zinc-400 hover:bg-white/5 transition-all duration-200">
          <Mail className="w-3.5 h-3.5" /> Open in Mail App
        </button>
        <button onClick={handleCopyDraft} data-testid="copy-draft-button"
          className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-sm border border-white/10 text-zinc-400 hover:bg-white/5 transition-all duration-200">
          {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
          {copied ? "Copied" : "Copy Draft"}
        </button>
      </div>
    </div>
  );
}

function TypingIndicator({ statusText }) {
  return (
    <div className="flex items-center gap-2 py-8" data-testid={CHAT.typingIndicator}>
      <span className="font-mono text-xs text-zinc-500 tracking-wider">
        {statusText || "PitchRoute is synthesizing"}
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

/* --- Live Execution Sidebar --- */
function ToolSidebar({ messages, liveSteps, liveStatus, isOpen, onToggle }) {
  // Get latest assistant metadata for completed responses
  const assistantMessages = messages.filter((m) => m.role === "assistant" && m.metadata);
  const latestMsg = assistantMessages[assistantMessages.length - 1];

  // Use live steps if available, else fall back to completed metadata
  const isLive = liveSteps.length > 0;
  const displaySteps = isLive ? liveSteps : (() => {
    if (!latestMsg?.metadata) return [];
    const tools = latestMsg.metadata.tool_used?.split(" → ") || [];
    const cats = latestMsg.metadata.category?.split(" → ") || [];
    return tools.map((t, i) => ({
      tool: t, category: cats[i] || "general", reason: "",
      status: "done",
    }));
  })();

  const meta = latestMsg?.metadata;

  if (displaySteps.length === 0 && !isLive) return null;

  return (
    <>
      <button onClick={onToggle} data-testid="sidebar-toggle"
        className="fixed top-4 right-4 z-50 p-2 rounded-sm bg-[#121214] border border-white/10 text-zinc-400 hover:text-white hover:border-white/20 transition-all duration-200"
        title={isOpen ? "Close execution panel" : "View execution plan"}>
        {isOpen ? <PanelRightClose className="w-4 h-4" /> : <PanelRightOpen className="w-4 h-4" />}
      </button>

      <div data-testid="tool-sidebar"
        className={`fixed top-0 right-0 h-full w-80 bg-[#0C0C0E] border-l border-white/[0.06] z-40 transition-transform duration-300 ease-out ${isOpen ? "translate-x-0" : "translate-x-full"}`}>
        <div className="h-full overflow-y-auto p-5 pt-16">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-mono text-[10px] uppercase tracking-[0.15em] text-zinc-600">Execution Plan</h3>
              {isLive && (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm bg-amber-400/10 border border-amber-400/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                  <span className="font-mono text-[9px] text-amber-400 uppercase">Live</span>
                </span>
              )}
            </div>
            <p className="text-xs text-zinc-500">
              {displaySteps.length > 1 ? `${displaySteps.length}-step pipeline` : "Single-step execution"}
            </p>
            {liveStatus && (
              <p className="font-mono text-[10px] text-zinc-500 mt-2 animate-pulse">{liveStatus}</p>
            )}
          </div>

          {/* Steps */}
          <div className="space-y-1" data-testid="execution-steps">
            {displaySteps.map((step, idx) => {
              const ToolIcon = TOOL_ICONS[step.tool] || CircleDot;
              const label = TOOL_LABELS[step.tool] || step.tool;
              const catLabel = CATEGORY_LABELS[step.category] || step.category;
              const status = step.status || "pending";

              const borderClass = status === "running" ? "border-amber-400/30 bg-amber-400/[0.03]"
                : status === "done" ? "border-white/[0.06] bg-[#121214]"
                : status === "error" ? "border-red-500/20 bg-red-500/[0.03]"
                : "border-white/[0.04] bg-[#0E0E10]";

              return (
                <div key={idx}>
                  <div className={`p-3 rounded-sm border transition-all duration-300 ${borderClass}`}
                    data-testid={`execution-step-${idx}`}>
                    <div className="flex items-center gap-2.5 mb-2">
                      <div className={`w-6 h-6 rounded-sm flex items-center justify-center flex-shrink-0 ${
                        status === "running" ? "bg-amber-400/20 border border-amber-400/40"
                        : status === "done" ? "bg-amber-400/10 border border-amber-400/20"
                        : "bg-white/5 border border-white/10"
                      }`}>
                        <span className={`font-mono text-[10px] font-medium ${
                          status === "running" ? "text-amber-400" : status === "done" ? "text-amber-400" : "text-zinc-600"
                        }`}>{idx + 1}</span>
                      </div>
                      <span className={`text-sm font-medium truncate ${
                        status === "pending" ? "text-zinc-600" : "text-white"
                      }`}>{label}</span>
                      <div className="ml-auto flex-shrink-0">
                        {status === "running" && <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />}
                        {status === "done" && <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />}
                        {status === "error" && <AlertCircle className="w-3.5 h-3.5 text-red-500" />}
                        {status === "pending" && <CircleDot className="w-3.5 h-3.5 text-zinc-700" />}
                      </div>
                    </div>

                    <div className="ml-8 space-y-1.5">
                      <div className="flex items-center gap-1.5">
                        <ToolIcon className={`w-3 h-3 ${status === "pending" ? "text-zinc-700" : "text-[#FF5500]"}`} />
                        <span className={`font-mono text-[10px] uppercase tracking-wider ${status === "pending" ? "text-zinc-700" : "text-[#FF5500]"}`}>
                          {step.tool}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <FolderOpen className={`w-3 h-3 ${status === "pending" ? "text-zinc-700" : "text-[#00C2FF]"}`} />
                        <span className={`font-mono text-[10px] uppercase tracking-wider ${status === "pending" ? "text-zinc-700" : "text-[#00C2FF]"}`}>
                          {catLabel}
                        </span>
                      </div>
                      {step.reason && (
                        <p className={`text-[10px] mt-1 ${status === "pending" ? "text-zinc-800" : "text-zinc-600"}`}>
                          {step.reason}
                        </p>
                      )}
                    </div>
                  </div>

                  {idx < displaySteps.length - 1 && (
                    <div className="flex justify-center py-1">
                      <ChevronRight className={`w-3.5 h-3.5 rotate-90 ${
                        displaySteps[idx + 1]?.status === "pending" ? "text-zinc-800" : "text-zinc-600"
                      }`} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Model & routing info */}
          {meta && (
            <>
              <Separator className="my-5 bg-white/[0.06]" />
              <div className="space-y-3">
                <div>
                  <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-zinc-600 block mb-1">Model</span>
                  <div className="flex items-center gap-1.5">
                    <Brain className="w-3 h-3 text-zinc-400" />
                    <span className="font-mono text-xs text-zinc-300">{meta.model_used}</span>
                  </div>
                </div>
                <div>
                  <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-zinc-600 block mb-1">Complexity</span>
                  <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-wider border-white/10 text-zinc-400">
                    {meta.complexity}
                  </Badge>
                </div>
                <div>
                  <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-zinc-600 block mb-1">Routing</span>
                  <span className="font-mono text-xs text-zinc-400">{meta.routing_source || "local"}</span>
                </div>
              </div>
            </>
          )}

          {/* Previous executions */}
          {assistantMessages.length > 1 && (
            <>
              <Separator className="my-5 bg-white/[0.06]" />
              <div>
                <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-zinc-600 block mb-3">Previous</span>
                <div className="space-y-2">
                  {assistantMessages.slice(0, -1).reverse().map((msg, idx) => {
                    const t = msg.metadata?.tool_used?.split(" → ") || ["none"];
                    return (
                      <div key={idx} className="p-2 rounded-sm border border-white/[0.04] bg-white/[0.02] text-xs">
                        <div className="flex items-center gap-1.5">
                          <Wrench className="w-3 h-3 text-zinc-600" />
                          <span className="font-mono text-[10px] text-zinc-500 uppercase truncate">{t.join(" → ")}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
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
          <button key={idx} onClick={() => onQuickAction(action.prompt)}
            data-testid={`${CHAT.quickActionChip}-${idx}`}
            className="quick-chip flex items-center gap-3 px-4 py-3 rounded-sm text-left text-sm transition-all duration-200 hover:border-white/30">
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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [liveSteps, setLiveSteps] = useState([]);
  const [liveStatus, setLiveStatus] = useState("");
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
    const updatedMessages = [...messages, { role: "user", content: userMsg }];
    setMessages(updatedMessages);
    setIsLoading(true);
    setLiveSteps([]);
    setLiveStatus("Analyzing request...");

    // Build history from current messages (last 10 messages for context)
    const history = updatedMessages
      .filter((m) => m.role === "user" || m.role === "assistant")
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content?.slice(0, 500) || "" }));

    try {
      const response = await fetch(`${API}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, history }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ") && eventType) {
            try {
              const data = JSON.parse(line.slice(6));
              handleSSEEvent(eventType, data);
            } catch (e) {
              // skip malformed events
            }
            eventType = "";
          }
        }
      }
    } catch (err) {
      console.error("SSE error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${err.message}`,
          metadata: { model_used: "N/A", tool_used: "none", category: "error", complexity: "N/A" },
        },
      ]);
    } finally {
      setIsLoading(false);
      setLiveSteps([]);
      setLiveStatus("");
      inputRef.current?.focus();
    }
  };

  const handleSSEEvent = useCallback((eventType, data) => {
    switch (eventType) {
      case "planning":
        setLiveStatus(data.status);
        break;

      case "plan":
        // Initialize all steps as "pending"
        const planned = data.steps.map((s) => ({
          tool: s.tool,
          category: s.category,
          reason: s.reason,
          status: "pending",
        }));
        setLiveSteps(planned);
        setLiveStatus(`${data.total_steps}-step plan ready`);
        if (data.total_steps > 1) {
          setSidebarOpen(true);
        }
        break;

      case "step_start":
        setLiveSteps((prev) =>
          prev.map((s, i) => i === data.step ? { ...s, status: "running" } : s)
        );
        setLiveStatus(`Running: ${TOOL_LABELS[data.tool] || data.tool}...`);
        // Open sidebar on first step if multiple
        setSidebarOpen(true);
        break;

      case "step_complete":
        setLiveSteps((prev) =>
          prev.map((s, i) =>
            i === data.step ? { ...s, status: data.status === "error" ? "error" : "done" } : s
          )
        );
        break;

      case "generating":
        setLiveStatus(data.status);
        break;

      case "done":
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.response,
            metadata: data.metadata,
            emailDraft: data.email_draft,
          },
        ]);
        setLiveStatus("");
        break;

      default:
        break;
    }
  }, []);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleQuickAction = (prompt) => {
    sendMessage(prompt);
  };

  const hasContent = messages.some((m) => m.role === "assistant" && m.metadata) || liveSteps.length > 0;

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
        <div ref={scrollRef}
          className={`h-full overflow-y-auto transition-all duration-300 ${sidebarOpen ? "mr-80" : ""}`}
          data-testid={CHAT.messageList}>
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
                      <AIResponse content={msg.content} metadata={msg.metadata} emailDraft={msg.emailDraft} />
                    )}
                  </div>
                ))}
                {isLoading && <TypingIndicator statusText={liveStatus} />}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tool Execution Sidebar */}
      {hasContent && (
        <ToolSidebar
          messages={messages}
          liveSteps={liveSteps}
          liveStatus={liveStatus}
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />
      )}

      {/* Input Bar */}
      <div className={`input-bar-glass border-t border-white/[0.06] p-4 sm:p-6 transition-all duration-300 ${sidebarOpen ? "mr-80" : ""}`} data-testid={CHAT.inputBar}>
        <div className="max-w-4xl mx-auto w-full">
          {messages.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {QUICK_ACTIONS.slice(0, 3).map((action, idx) => (
                <button key={idx} onClick={() => handleQuickAction(action.prompt)}
                  data-testid={`${CHAT.quickActionChip}-inline-${idx}`}
                  className="quick-chip inline-flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs"
                  disabled={isLoading}>
                  <action.icon className="w-3 h-3" />
                  {action.label}
                </button>
              ))}
            </div>
          )}

          <div className="input-container-focus flex items-center gap-2 bg-[#121214] border border-white/[0.08] rounded-sm px-4 py-2.5">
            <Sparkles className="w-4 h-4 text-zinc-600 flex-shrink-0" />
            <input ref={inputRef} type="text" value={input}
              onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
              placeholder="Ask PitchRoute anything..."
              className="flex-1 bg-transparent border-none outline-none text-sm text-white placeholder:text-zinc-600 font-body"
              disabled={isLoading} data-testid={CHAT.inputField} />
            <Button size="icon" variant="ghost" onClick={() => sendMessage()}
              disabled={!input.trim() || isLoading} data-testid={CHAT.sendButton}
              className="h-8 w-8 text-zinc-500 hover:text-amber-400 hover:bg-amber-400/10 rounded-sm transition-all duration-200 disabled:opacity-30">
              {isLoading ? <ArrowRight className="w-4 h-4 animate-pulse" /> : <Send className="w-4 h-4" />}
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
