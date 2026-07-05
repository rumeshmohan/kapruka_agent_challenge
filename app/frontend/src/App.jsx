import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { OrderTrackingCard, PackageIcon, CheckCircleIcon } from './OrderTrackingCard.jsx';
import PaymentPage from './PaymentPage.jsx';
import TrackPage from './TrackPage.jsx';

// Subtle chat wallpaper: a tiled pattern of gift boxes & shopping bags,
// intuitive for a gifting assistant, colored per theme so it reads
// clearly on both light and dark backgrounds without being distracting.
const buildWallpaper = (strokeColor) => {
  const svg = `
    <svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'>
      <g fill='none' stroke='${strokeColor}' stroke-width='1.4' stroke-linecap='round' stroke-linejoin='round'>
        <path d='M14 34h16l1.6 22h-19.2z'/>
        <path d='M17.5 34v-3.2a4.5 4.5 0 0 1 9 0V34'/>
        <rect x='64' y='18' width='18' height='15' rx='1.5'/>
        <path d='M64 24h18M73 18v15'/>
        <path d='M27 76a9 9 0 1 0 0.1 0z'/>
        <path d='M22 71l10 10M32 71l-10 10'/>
        <rect x='78' y='70' width='20' height='16' rx='1.5'/>
        <path d='M78 76.5h20M88 70v16'/>
        <path d='M88 70l3-5h-6z'/>
      </g>
    </svg>`;
  return `data:image/svg+xml,${encodeURIComponent(svg.replace(/\s+/g, ' '))}`;
};

// Online shopping agent icon: shopping bag with a green "online" dot,
// so the header clearly reads as a live shopping assistant.
const ShoppingAgentIcon = ({ size = 22, color = '#fff' }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Shopping bag body */}
    <path
      fill={color}
      d="M9.5 11.5h13l1.1 15.4c.07.99-.71 1.85-1.71 1.85H10.1c-1 0-1.78-.86-1.71-1.85l1.11-15.4z"
    />
    {/* Bag handle */}
    <path
      d="M12.5 11.5v-1.8a3.5 3.5 0 0 1 7 0v1.8"
      stroke={color}
      strokeWidth="1.8"
      fill="none"
      strokeLinecap="round"
    />
    {/* Online status dot */}
    <circle cx="23.5" cy="9" r="4.2" fill="#00e676" stroke={color} strokeWidth="1.1" />
  </svg>
);

// Inline mic icons (no external font dependency, so they always render)
const MicIcon = ({ size = 18, color = '#fff' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3z" fill={color} />
    <path d="M19 11a7 7 0 0 1-14 0" stroke={color} strokeWidth="1.8" strokeLinecap="round" fill="none" />
    <path d="M12 18v3" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
    <path d="M8.5 21h7" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

const MicOffIcon = ({ size = 18, color = '#fff' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 15a3 3 0 0 0 3-3V9.5l-5.7-5.7A3 3 0 0 1 15 6v6c0 .34-.04.67-.12.98" stroke={color} strokeWidth="1.8" strokeLinecap="round" fill="none" />
    <path d="M9 9v3a3 3 0 0 0 4.24 2.74" stroke={color} strokeWidth="1.8" strokeLinecap="round" fill="none" />
    <path d="M19 11a7 7 0 0 1-1.34 4.12" stroke={color} strokeWidth="1.8" strokeLinecap="round" fill="none" />
    <path d="M5 11a7 7 0 0 0 9.9 6.36" stroke={color} strokeWidth="1.8" strokeLinecap="round" fill="none" />
    <path d="M12 18v3" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
    <path d="M8.5 21h7" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
    <path d="M3 3l18 18" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

const SendIcon = ({ size = 18, color = '#fff' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3.4 20.6L21 12 3.4 3.4 3 10l12 2-12 2z" fill={color} />
  </svg>
);

// Simple user avatar icon (person silhouette)
const UserAvatarIcon = ({ size = 18, color = '#fff' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="8" r="4" fill={color} />
    <path d="M4 20c0-4 3.6-6.5 8-6.5s8 2.5 8 6.5" fill={color} />
  </svg>
);

// Refresh / restart-chat icon (circular arrow)
const RefreshIcon = ({ size = 16, color = '#fff' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M20 11A8 8 0 1 0 18.5 16" stroke={color} strokeWidth="2" strokeLinecap="round" fill="none" />
    <path d="M20 5v6h-6" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
  </svg>
);


function ChatPage() {
  const navigate = useNavigate();

  // Greeting text is keyed by dialect, not auto-cycled. Warm, welcoming,
  // distinctly Sri Lankan tone — like a friendly neighborhood shop assistant.
  const greetingByDialect = {
    'en-US': "Ayubowan! 🌺 Warm greetings from Kapruka — so happy you dropped by! Whether it's a birthday, an anniversary, or just a little something to say 'I'm thinking of you,' I'm here to help you find the perfect gift. Tell me who it's for and the occasion, or use the filters on the left to get started. 🎁",
    'si-LK': "ආයුබෝවන්! 🌺 කප්රුකට සාදරයෙන් පිළිගනිමු — ඔබ මෙහි පැමිණීම ගැන සතුටුයි! උපන්දිනයක්ද, විවාහ සංවත්සරයක්ද, නැත්නම් 'ඔබ මතකයි' කියන්න විශේෂ තෑග්ගක්ද — ඕනෑම අවස්ථාවකට ගැලපෙන අලංකාර තෑග්ගක් සොයාගැනීමට මම උදව් කරන්නම්. එය කාටද, මොකද අවස්ථාව කියල මට ටිකක් කියන්න, නැත්නම් වම් පැත්තේ ෆිල්ටර් පාවිච්චි කරන්න. 🎁",
    'ta-LK': "வணக்கம்! 🌺 கப்ருகாவிற்கு அன்பான வரவேற்பு — நீங்கள் வந்ததில் மிக்க மகிழ்ச்சி! பிறந்தநாளாக இருந்தாலும், திருமண நாள் ஆனாலும், அல்லது 'நீங்கள் நினைவில் இருக்கிறீர்கள்' என்று சொல்ல ஒரு சிறிய பரிசு ஆனாலும் — ஒவ்வொரு தருணத்திற்கும் ஏற்ற அழகான பரிசை கண்டுபிடிக்க நான் உதவுகிறேன். அது யாருக்கு, என்ன சந்தர்ப்பம் என்று கொஞ்சம் சொல்லுங்கள், அல்லது இடதுபுறம் உள்ள வடிகட்டிகளைப் பயன்படுத்துங்கள். 🎁"
  };
  const getGreeting = (dialect) => greetingByDialect[dialect] || greetingByDialect['en-US'];

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      isGreeting: true,
      content: getGreeting('en-US')
    }
  ]);
  const [input, setInput] = useState('');
  const [profile, setProfile] = useState({ customer_name: 'Guest', recipients: {} });
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingLabel, setLoadingLabel] = useState('🎁 Hunting down the perfect gift for you...');
  const [notifications, setNotifications] = useState([]);

  const [keyword, setKeyword] = useState('');
  const [occasion, setOccasion] = useState('None');
  const [maxBudget, setMaxBudget] = useState(25000);
  const [sortBy, setSortBy] = useState('Best Match');

  const [selectedDialect, setSelectedDialect] = useState('en-US');
  const [isListening, setIsListening] = useState(false);

  const [chatTheme, setChatTheme] = useState('dark');

  // Per-product quantity picker state (keyed by product id) used on the
  // catalog cards so a user can choose how many of an item to add at once.
  const [productQty, setProductQty] = useState({});
  const getProductQty = (id) => productQty[id] || 1;
  const bumpProductQty = (id, delta) => {
    setProductQty(prev => {
      const next = Math.max(1, (prev[id] || 1) + delta);
      return { ...prev, [id]: next };
    });
  };

  const brandNames = ["Kapruka", "කප්රුක", "கப்ருகா"];

  const [langIndex, setLangIndex] = useState(0);
  const brandIndex = langIndex;

  useEffect(() => {
    const interval = setInterval(() => {
      setLangIndex((prev) => (prev + 1) % brandNames.length);
    }, 3500);
    return () => clearInterval(interval);
  }, []);

  // Whenever the dialect dropdown changes, update the greeting bubble (only
  // while it's still the sole/greeting message) to match the chosen language.
  useEffect(() => {
    setMessages((prev) => {
      if (prev.length === 1 && prev[0].isGreeting) {
        return [{ ...prev[0], content: getGreeting(selectedDialect) }];
      }
      return prev;
    });
  }, [selectedDialect]);

  const sessionId = "session_user_hf";

  // Demo test order number provided for the Kapruka Agent Challenge tracking flow.
  const TEST_ORDER_NUMBER = 'VPAY827982BA';

  const fetchProfile = async () => {
    try {
      const res = await fetch('/api/profile');
      const data = await res.json();
      setProfile(data);
    } catch (e) { console.error("Profile sync failure", e); }
  };

  useEffect(() => { fetchProfile(); }, []);

  useEffect(() => {
    const bg = chatTheme === 'dark' ? '#0b141a' : '#e5ddd5';
    const thumb = chatTheme === 'dark' ? '#3b4a54' : '#c7ccd1';
    const track = chatTheme === 'dark' ? '#0b141a' : '#e5ddd5';

    document.documentElement.style.margin = '0';
    document.documentElement.style.padding = '0';
    document.documentElement.style.height = '100%';
    document.documentElement.style.backgroundColor = bg;
    document.documentElement.style.colorScheme = chatTheme === 'dark' ? 'dark' : 'light';
    document.body.style.margin = '0';
    document.body.style.padding = '0';
    document.body.style.height = '100%';
    document.body.style.backgroundColor = bg;

    let styleTag = document.getElementById('theme-scrollbar-style');
    if (!styleTag) {
      styleTag = document.createElement('style');
      styleTag.id = 'theme-scrollbar-style';
      document.head.appendChild(styleTag);
    }
    styleTag.innerHTML = `
      * { scrollbar-color: ${thumb} ${track}; scrollbar-width: thin; }
      *::-webkit-scrollbar { width: 10px; height: 10px; }
      *::-webkit-scrollbar-track { background: ${track}; }
      *::-webkit-scrollbar-thumb { background-color: ${thumb}; border-radius: 8px; border: 2px solid ${track}; }
      *::-webkit-scrollbar-thumb:hover { background-color: ${chatTheme === 'dark' ? '#54646f' : '#a8afb6'}; }
      @keyframes onlinePulse {
        0% { box-shadow: 0 0 0 0 rgba(0,230,118,0.55); }
        70% { box-shadow: 0 0 0 6px rgba(0,230,118,0); }
        100% { box-shadow: 0 0 0 0 rgba(0,230,118,0); }
      }
      @keyframes greetingFade {
        0% { opacity: 0; }
        100% { opacity: 1; }
      }
    `;
  }, [chatTheme]);

  useEffect(() => {
    if (input.trim() || keyword || occasion !== 'None') {
      handleSendMessage();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDialect]);

  const toggleVoiceTranscription = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("⚠️ Local Web Speech APIs are not supported in your current browser architecture. Try Google Chrome.");
      return;
    }
    if (isListening) {
      setIsListening(false);
      return;
    }

    setInput('');

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = selectedDialect;

    recognition.onstart = () => setIsListening(true);
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = (event) => {
      const liveTranscript = event.results[0][0].transcript;
      setInput(liveTranscript);
    };
    recognition.start();
  };

  const handleSendMessage = async (forcedQuery = null) => {
    const textToSend = forcedQuery || input;
    if (!textToSend.trim() && !keyword && occasion === 'None') return;

    let finalQuery = textToSend;
    if (!finalQuery.trim()) {
      let contextualChunks = [];
      if (keyword) contextualChunks.push(keyword);
      if (occasion !== 'None') contextualChunks.push(`suitable for ${occasion}`);
      finalQuery = `Show me products related to: ${contextualChunks.join(' ')}`;
    }

    setMessages(prev => [...prev, { role: 'user', content: finalQuery }]);
    setInput('');

    // Vary the wait-time message by intent so it doesn't always say
    // "hunting down the perfect gift" for things like order tracking.
    if (/vpay\d+[a-zA-Z0-9]*/i.test(finalQuery)) {
      setLoadingLabel('📦 Checking your order status...');
    } else if (/track|delivery|deliver|shipped|shipping/i.test(finalQuery)) {
      setLoadingLabel('🚚 Looking up delivery details...');
    } else if (/cart|checkout|payment|pay now/i.test(finalQuery)) {
      setLoadingLabel('🧾 Working on your order...');
    } else {
      setLoadingLabel('🎁 Hunting down the perfect gift for you...');
    }
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: finalQuery, session_id: sessionId, cart })
      });
      const data = await res.json();

      let processedProds = data.products || [];
      processedProds = processedProds.filter(p => {
        const pVal = parseFloat(String(p.price || 0).replace(/[^0-9.]/g, ''));
        return pVal <= maxBudget;
      });

      if (sortBy === 'Price: Low to High') {
        processedProds.sort((a, b) => parseFloat(a.price) - parseFloat(b.price));
      } else if (sortBy === 'Price: High to Low') {
        processedProds.sort((a, b) => parseFloat(b.price) - parseFloat(a.price));
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.text,
        products: processedProds,
        orderStatus: data.order_status || null
      }]);
      fetchProfile();

      // Checkout completed server-side: hand off to a dedicated full-page
      // payment step instead of leaving the raw link buried in the chat.
      if (data.checkout_data && data.checkout_data.checkout_url) {
        navigate('/payment', { state: { checkoutData: data.checkout_data } });
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Server connection timed out.' }]);
    } finally {
      setLoading(false);
    }
  };

  // Quick action: fires off a canned "track my order" query using the
  // demo test order number, so the tracking flow can be triggered in one tap.
  const handleTrackDemoOrder = () => {
    handleSendMessage(`Where is my order ${TEST_ORDER_NUMBER}?`);
  };

  const addToCart = (item, qty = 1) => {
    const addQty = Math.max(1, qty);
    setCart(prev => {
      const existing = prev.find(c => c.id === item.id);
      if (existing) {
        return prev.map(c => c.id === item.id ? { ...c, qty: c.qty + addQty } : c);
      }
      return [...prev, { ...item, qty: addQty }];
    });

    const id = Date.now();
    const newNotification = { id, message: `🛒 Added ${addQty > 1 ? `${addQty}x ` : ''}"${item.name}" to cart!` };
    setNotifications(prev => [...prev, newNotification]);

    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 3000);

    // Reset that product's picker back to 1 after adding
    setProductQty(prev => ({ ...prev, [item.id]: 1 }));
  };

  const updateQty = (itemId, delta) => {
    setCart(prev => {
      return prev
        .map(c => c.id === itemId ? { ...c, qty: c.qty + delta } : c)
        .filter(c => c.qty > 0);
    });
  };

  const clearSearch = () => {
    setKeyword('');
    setOccasion('None');
    setMaxBudget(25000);
    setSortBy('Best Match');
  };

  // Profile-only reset: rolls the sidebar profile back to Guest defaults.
  // Does not touch the cart, search filters, or chat stream.
  const handleProfileReset = async () => {
    try {
      const res = await fetch('/api/profile/reset', { method: 'POST' });
      const data = await res.json();
      setProfile(data);
    } catch (e) {
      console.error("Profile reset failure", e);
      // Fall back to a local-only reset if the backend call fails, so the
      // UI still reflects the intent even if the persisted copy didn't update.
      setProfile({ customer_name: 'Guest', recipients: {} });
    }

    const id = Date.now();
    setNotifications(prev => [...prev, { id, message: "👤 Profile reset to Guest!" }]);
    setTimeout(() => setNotifications(prev => prev.filter(n => n.id !== id)), 2500);
  };

  // Resets the chat area back to just the initial greeting (in whatever
  // language is currently selected). Does not touch cart, filters, or profile.
  const handleRestartChat = () => {
    setMessages([{ role: 'assistant', isGreeting: true, content: getGreeting(selectedDialect) }]);
    setInput('');
  };

  const clearCart = () => {
    if (cart.length === 0) return;
    setCart([]);
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message: `🧹 Cart cleared!` }]);
    setTimeout(() => setNotifications(prev => prev.filter(n => n.id !== id)), 3000);
  };

  const handleCheckout = () => {
    if (cart.length === 0) return;
    // Demo flow: build a dummy order summary from the cart locally (no
    // backend call) and go straight to the payment page. Pay Now there
    // simulates success and hands off to the existing track-order page.
    const itemsTotal = cart.reduce(
      (sum, item) => sum + (parseFloat(item.price) || 0) * (item.quantity || 1),
      0
    );
    const dummyCheckoutData = {
      checkout_url: null, // no real gateway in this demo flow
      order_ref: TEST_ORDER_NUMBER,
      summary: {
        items_total: itemsTotal,
        delivery_fee: 0,
        addons_total: 0,
        grand_total: itemsTotal,
        currency: 'LKR',
      },
      expires_at: null,
    };
    navigate('/payment', { state: { checkoutData: dummyCheckoutData } });
  };

  const cartSubtotal = cart.reduce((sum, item) => sum + parseFloat(item.price || 0) * (item.qty || 1), 0);
  const deliveryHandlingFee = cartSubtotal * 0.10;
  const cartGrandTotal = cartSubtotal + deliveryHandlingFee;

  const themePalettes = {
    dark: {
      pageBg: '#0f172a',
      pageText: '#f8fafc',
      sidebarBg: '#1e293b',
      sidebarBorder: '#334155',
      cardBg: '#111827',
      cardBorder: '#334155',
      textMuted: '#94a3b8',
      textFaint: '#64748b',
      labelText: '#cbd5e1',
      fieldBg: '#0f172a',
      fieldBorder: '#475569',
      fieldText: '#ffffff',
      chatBg: '#0b141a',
      chatBgTint: 'rgba(11,20,26,0.94)',
      pattern: buildWallpaper('#24333b'),
      patternOpacity: 0.5,
      bubbleUserBg: '#005c4b',
      bubbleUserText: '#e9edef',
      bubbleAgentBg: '#202c33',
      bubbleAgentBorder: '#2a3942',
      bubbleAgentText: '#e9edef',
      headerBg: '#202c33',
      headerText: '#e9edef',
      headerSubText: '#8696a0',
      inputBarBg: '#202c33',
      searchBg: '#2a3942',
      searchBorder: '#2a3942',
      inlineText: '#e9edef',
      accent: '#00a884',
      productCardBg: '#1f2c34',
      productCardBorder: '#2a3942',
      tagWarnBg: '#451a03',
      tagWarnText: '#f59e0b',
      tagWarnBorder: '#78350f',
      tagPrefBg: '#172554',
      tagPrefText: '#60a5fa',
      tagPrefBorder: '#1e3a8a'
    },
    light: {
      pageBg: '#f0f2f5',
      pageText: '#111b21',
      sidebarBg: '#ffffff',
      sidebarBorder: '#e9edef',
      cardBg: '#f7f8fa',
      cardBorder: '#e2e5e9',
      textMuted: '#667781',
      textFaint: '#8696a0',
      labelText: '#3b4a54',
      fieldBg: '#ffffff',
      fieldBorder: '#cfd4d9',
      fieldText: '#111b21',
      chatBg: '#e5ddd5',
      chatBgTint: 'rgba(229,221,213,0.88)',
      pattern: buildWallpaper('#c9cfd6'),
      patternOpacity: 0.6,
      bubbleUserBg: '#d9fdd3',
      bubbleUserText: '#111b21',
      bubbleAgentBg: '#ffffff',
      bubbleAgentBorder: '#e9edef',
      bubbleAgentText: '#111b21',
      headerBg: '#008069',
      headerText: '#ffffff',
      headerSubText: '#d8f0ea',
      inputBarBg: '#f0f2f5',
      searchBg: '#ffffff',
      searchBorder: '#e9edef',
      inlineText: '#111b21',
      accent: '#00a884',
      productCardBg: '#ffffff',
      productCardBorder: '#e9edef',
      tagWarnBg: '#fff3e0',
      tagWarnText: '#b45309',
      tagWarnBorder: '#fcd9a8',
      tagPrefBg: '#e8f0fe',
      tagPrefText: '#1d4ed8',
      tagPrefBorder: '#bfdbfe'
    }
  };
  const wa = themePalettes[chatTheme];

  const styles = {
    container: { display: 'flex', width: '100%', height: '100vh', backgroundColor: wa.pageBg, color: wa.pageText, fontFamily: 'system-ui, sans-serif', position: 'relative', transition: 'background-color 0.2s, color 0.2s', boxSizing: 'border-box' },
    sidebar: { width: '340px', backgroundColor: wa.sidebarBg, borderRight: `1px solid ${wa.sidebarBorder}`, padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' },

    main: { flex: 1, display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: wa.chatBg, position: 'relative' },
    chatStream: {
      flex: 1,
      padding: '24px',
      overflowY: 'auto',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px',
      backgroundColor: wa.chatBg,
      backgroundImage: `linear-gradient(${wa.chatBgTint}, ${wa.chatBgTint}), url('${wa.pattern}')`,
      backgroundBlendMode: 'normal',
      backgroundRepeat: 'no-repeat, repeat',
      backgroundSize: 'auto, 120px',
      position: 'relative'
    },

    bubbleUser: { alignSelf: 'flex-end', backgroundColor: wa.bubbleUserBg, color: wa.bubbleUserText, padding: '12px 16px', borderRadius: '16px 16px 0 16px', maxWidth: '70%', fontSize: '14px', boxShadow: '0 1px 0.5px rgba(11,20,26,.13)', position: 'relative', zIndex: 1 },
    bubbleAgent: { alignSelf: 'flex-start', backgroundColor: wa.bubbleAgentBg, border: `1px solid ${wa.bubbleAgentBorder}`, color: wa.bubbleAgentText, padding: '12px 16px', borderRadius: '16px 16px 16px 0', maxWidth: '75%', fontSize: '14px', boxShadow: '0 1px 0.5px rgba(11,20,26,.13)', position: 'relative', zIndex: 1 },

    card: { backgroundColor: wa.cardBg, borderRadius: '12px', border: `1px solid ${wa.cardBorder}`, padding: '14px' },
    sectionTitle: { fontSize: '11px', textTransform: 'uppercase', tracking: '0.1em', color: wa.textMuted, fontWeight: 'bold', marginBottom: '10px', display: 'block' },
    label: { fontSize: '12px', color: wa.labelText, fontWeight: '500', display: 'block', marginBottom: '6px' },
    input: { width: '100%', boxSizing: 'border-box', backgroundColor: wa.fieldBg, border: `1px solid ${wa.fieldBorder}`, borderRadius: '8px', padding: '8px 12px', color: wa.fieldText, fontSize: '13px', marginBottom: '12px' },
    btnPrimary: { width: '100%', background: `linear-gradient(135deg, ${wa.accent}, #06997a)`, border: 'none', color: '#fff', padding: '10px', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', fontSize: '13px' },
    inputDeckContainer: { padding: '16px 24px', borderTop: `1px solid ${wa.bubbleAgentBorder}`, backgroundColor: wa.inputBarBg },
    searchBarWrapper: { display: 'flex', alignItems: 'center', backgroundColor: wa.searchBg, border: `1px solid ${wa.searchBorder}`, borderRadius: '12px', padding: '4px 8px', gap: '8px' },
    inlineInput: { flex: 1, backgroundColor: 'transparent', border: 'none', color: wa.inlineText, padding: '10px', fontSize: '14px', outline: 'none' },
    inlineSelect: { backgroundColor: wa.searchBg, border: `1px solid ${wa.accent}`, color: wa.inlineText, fontSize: '12px', borderRadius: '6px', padding: '6px 10px', outline: 'none', cursor: 'pointer' },
    micButton: { display: 'flex', alignItems: 'center', justifyContent: 'center', border: 'none', borderRadius: '8px', width: '36px', height: '36px', fontSize: '16px', cursor: 'pointer', transition: 'all 0.2s' },
    sendButton: { background: `linear-gradient(135deg, ${wa.accent}, #06997a)`, color: '#fff', border: 'none', borderRadius: '8px', padding: '8px 18px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer', height: '36px' },
    toastContainer: { position: 'absolute', top: '20px', right: '20px', zIndex: '9999', display: 'flex', flexDirection: 'column', gap: '10px' },
    toastItem: { backgroundColor: wa.accent, color: '#fff', padding: '12px 20px', borderRadius: '8px', fontSize: '13px', fontWeight: 'bold', boxShadow: '0 4px 12px rgba(0,0,0,0.3)' },
    brandHeader: { padding: '16px 24px', borderBottom: `1px solid ${wa.bubbleAgentBorder}`, background: wa.headerBg, display: 'flex', alignItems: 'center', gap: '14px', justifyContent: 'space-between' },
    brandHeaderLeft: { display: 'flex', alignItems: 'center', gap: '14px' },
    brandIconWrap: { backgroundColor: chatTheme === 'dark' ? wa.accent : 'rgba(255,255,255,0.2)', padding: '8px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', boxSizing: 'border-box' },
    brandTitleText: { margin: 0, fontSize: '18px', fontWeight: '900', color: wa.headerText, letterSpacing: '-0.02em' },
    tickerSpan: { color: chatTheme === 'dark' ? '#eab308' : '#ffe38a', display: 'inline-block', transition: 'all 0.4s ease', textShadow: '0 0 10px rgba(234,179,8,0.2)' },
    calcLine: { display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px', color: wa.labelText },
    themeToggleWrap: { display: 'flex', backgroundColor: 'rgba(255,255,255,0.12)', borderRadius: '20px', padding: '3px', gap: '2px' },
    themeToggleBtn: (active) => ({
      border: 'none', borderRadius: '18px', padding: '6px 12px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer',
      backgroundColor: active ? '#ffffff' : 'transparent',
      color: active ? '#111b21' : wa.headerText,
      transition: 'all 0.2s'
    }),
    qtyStepperBtn: { width: '22px', height: '22px', borderRadius: '4px', border: `1px solid ${wa.fieldBorder}`, background: 'transparent', color: wa.labelText, fontSize: '13px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', lineHeight: 1, padding: 0 },
    trackOrderBtn: { display: 'flex', alignItems: 'center', gap: '6px', border: `1px solid ${wa.fieldBorder}`, background: 'transparent', color: wa.labelText, padding: '8px 12px', borderRadius: '8px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }
  };

  return (
    <div style={styles.container}>

      <div style={styles.toastContainer}>
        {notifications.map(n => <div key={n.id} style={styles.toastItem}>{n.message}</div>)}
      </div>

      <div style={styles.sidebar}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ backgroundColor: wa.accent, width: '36px', height: '36px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <ShoppingAgentIcon size={18} color="#ffffff" />
          </div>
          <div>
            <h2 style={{ fontSize: '17px', fontWeight: '800', margin: '0 0 2px 0', color: wa.pageText }}>Gift Finder Assistant</h2>
            <p style={{ fontSize: '11px', color: wa.textMuted, margin: 0 }}>Refine your search & track your basket</p>
          </div>
        </div>

        <div style={styles.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span style={{ ...styles.sectionTitle, marginBottom: 0 }}>👤 Your Profile</span>
            <button
              onClick={handleProfileReset}
              title="Reset profile to Guest"
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                width: '26px', height: '26px', borderRadius: '50%', border: `1px solid ${wa.cardBorder}`,
                backgroundColor: 'transparent', cursor: 'pointer'
              }}
            >
              <RefreshIcon size={13} color={wa.textMuted} />
            </button>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: wa.accent, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: '#fff' }}>G</div>
            <div>
              <p style={{ fontSize: '13px', fontWeight: 'bold', margin: 0, color: wa.pageText }}>{profile.customer_name}</p>
              <p style={{ fontSize: '10px', color: wa.textFaint, margin: 0 }}>Signed in</p>
            </div>
          </div>

          {profile.recipients && Object.keys(profile.recipients).length > 0 && (
            <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: `1px solid ${wa.cardBorder}` }}>
              {Object.entries(profile.recipients).map(([name, data]) => (
                <div key={name} style={{ marginBottom: '8px', fontSize: '12px' }}>
                  <span style={{ color: '#f472b6', fontWeight: 'bold', textTransform: 'capitalize' }}>💝 {name}:</span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                    {data.allergies?.map(a => <span key={a} style={{ fontSize: '9px', backgroundColor: wa.tagWarnBg, color: wa.tagWarnText, padding: '2px 6px', borderRadius: '4px', border: `1px solid ${wa.tagWarnBorder}` }}>⚠️ {a}</span>)}
                    {data.preferences?.map(p => <span key={p} style={{ fontSize: '9px', backgroundColor: wa.tagPrefBg, color: wa.tagPrefText, padding: '2px 6px', borderRadius: '4px', border: `1px solid ${wa.tagPrefBorder}` }}>❤️ {p}</span>)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={styles.card}>
          <span style={styles.sectionTitle}>🔍 Search Filters</span>

          <label style={styles.label}>Immediate Keyword Search</label>
          <input type="text" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="e.g. Cakes, Lilies, Toys" style={styles.input} />

          <label style={styles.label}>Filter Occasion</label>
          <select value={occasion} onChange={(e) => setOccasion(e.target.value)} style={styles.input}>
            <option value="None">None (All Catalogs)</option>
            <option value="Birthday Celebration">Birthday Celebration</option>
            <option value="Anniversary Gift">Anniversary Gift</option>
            <option value="Christmas Hamper">Christmas Hamper</option>
            <option value="Mother's Day">Mother's Day</option>
          </select>

          <label style={styles.label}>Max Budget: LKR {maxBudget.toLocaleString()}</label>
          <input type="range" min="500" max="100000" step="500" value={maxBudget} onChange={(e) => setMaxBudget(Number(e.target.value))} style={{ width: '100%', marginBottom: '16px', accentColor: wa.accent }} />

          <label style={styles.label}>Sort Layout By</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} style={styles.input}>
            <option value="Best Match">Best Match</option>
            <option value="Price: Low to High">Price: Low to High</option>
            <option value="Price: High to Low">Price: High to Low</option>
          </select>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={() => handleSendMessage()} style={{ ...styles.btnPrimary, flex: 2 }}>🔎 Search Gifts</button>
            <button
              onClick={clearSearch}
              style={{
                flex: 1, background: 'transparent', border: `1px solid ${wa.fieldBorder}`, color: wa.labelText,
                padding: '10px', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', fontSize: '13px'
              }}
            >
              ✕ Clear
            </button>
          </div>
        </div>

        <div style={styles.card}>
          <span style={styles.sectionTitle}>📦 Order Tracking</span>
          <p style={{ fontSize: '11px', color: wa.textFaint, margin: '0 0 10px 0' }}>
            Already checked out? Track your delivery status live.
          </p>
          <button onClick={handleTrackDemoOrder} style={styles.trackOrderBtn}>
            <PackageIcon size={14} color={wa.accent} />
            Track my order
          </button>
        </div>

        <div style={{ ...styles.card, marginTop: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span style={{ ...styles.sectionTitle, marginBottom: 0 }}>🧮 Your Cart</span>
          </div>

          <div style={{ maxHeight: '140px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '10px' }}>
            {cart.length === 0 ? <p style={{ fontSize: '11px', color: wa.textFaint, textAlign: 'center', margin: '6px 0' }}>No products inside basket.</p> :
              cart.map((c, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', backgroundColor: wa.fieldBg, padding: '6px 8px', borderRadius: '4px', color: wa.pageText, gap: '8px' }}>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>{c.name}</span>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                    <button onClick={() => updateQty(c.id, -1)} style={styles.qtyStepperBtn}>−</button>
                    <span style={{ minWidth: '14px', textAlign: 'center', fontWeight: 'bold' }}>{c.qty || 1}</span>
                    <button onClick={() => updateQty(c.id, 1)} style={styles.qtyStepperBtn}>+</button>
                  </div>

                  <span style={{ color: wa.accent, fontWeight: 'bold', flexShrink: 0, minWidth: '70px', textAlign: 'right' }}>
                    Rs. {(parseFloat(c.price || 0) * (c.qty || 1)).toLocaleString()}
                  </span>
                </div>
              ))}

          </div>

          <div style={{ paddingTop: '10px', borderTop: `1px solid ${wa.cardBorder}` }}>
            <div style={styles.calcLine}>
              <span>Subtotal:</span>
              <span>LKR {cartSubtotal.toLocaleString()}</span>
            </div>
            <div style={styles.calcLine}>
              <span>Delivery & Handling (10%):</span>
              <span>LKR {deliveryHandlingFee.toLocaleString()}</span>
            </div>
            <div style={{ ...styles.calcLine, fontSize: '13px', fontWeight: 'bold', color: '#eab308', marginTop: '4px' }}>
              <span>Grand Total:</span>
              <span>LKR {cartGrandTotal.toLocaleString()}</span>
            </div>

            <button
              onClick={handleCheckout}
              disabled={cart.length === 0}
              style={{
                width: '100%', marginTop: '10px', border: 'none', borderRadius: '8px', padding: '11px',
                fontWeight: 'bold', fontSize: '13px', color: '#fff',
                background: cart.length === 0 ? '#475569' : `linear-gradient(135deg, ${wa.accent}, #06997a)`,
                cursor: cart.length === 0 ? 'not-allowed' : 'pointer',
                opacity: cart.length === 0 ? 0.6 : 1
              }}
            >
              🛍️ Buy Now
            </button>

            {cart.length > 0 && (
              <button
                onClick={clearCart}
                style={{
                  width: '100%', marginTop: '8px', background: 'transparent', border: `1px solid ${wa.fieldBorder}`, color: wa.labelText,
                  padding: '8px', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', fontSize: '12px'
                }}
              >
                🧹 Clear Cart
              </button>
            )}
          </div>
        </div>
      </div>

      <div style={styles.main}>

        <div style={styles.brandHeader}>
          <div style={styles.brandHeaderLeft}>
            <div style={styles.brandIconWrap}>
              <ShoppingAgentIcon size={20} color={chatTheme === 'dark' ? '#0b141a' : '#ffffff'} />
            </div>
            <div>
              <h1 style={styles.brandTitleText}>
                Kapi - <span style={styles.tickerSpan}>{brandNames[brandIndex]}</span> AI Shopping Agent
              </h1>
              <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: wa.headerSubText, fontWeight: '500', display: 'flex', alignItems: 'center', gap: '6px' }}>
                Your Shopping Assistant
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{
                    width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#00e676',
                    boxShadow: '0 0 0 rgba(0,230,118,0.6)', animation: 'onlinePulse 1.6s infinite'
                  }} />
                  Online
                </span>
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={handleRestartChat}
              title="Restart chat"
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                width: '34px', height: '34px', borderRadius: '50%', border: 'none',
                backgroundColor: 'rgba(255,255,255,0.12)', cursor: 'pointer', transition: 'background-color 0.2s'
              }}
            >
              <RefreshIcon size={16} color={wa.headerText} />
            </button>
            <div style={styles.themeToggleWrap}>
              <button style={styles.themeToggleBtn(chatTheme === 'dark')} onClick={() => setChatTheme('dark')}>Dark</button>
              <button style={styles.themeToggleBtn(chatTheme === 'light')} onClick={() => setChatTheme('light')}>Light</button>
            </div>
          </div>
        </div>

        <div style={styles.chatStream}>
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                alignItems: 'flex-end',
                gap: '8px',
                position: 'relative',
                zIndex: 1
              }}
            >
              <div style={{
                width: '30px', height: '30px', borderRadius: '50%', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                backgroundColor: msg.role === 'user' ? '#475569' : wa.accent,
                boxShadow: '0 1px 2px rgba(0,0,0,0.25)'
              }}>
                {msg.role === 'user'
                  ? <UserAvatarIcon size={16} color="#fff" />
                  : <ShoppingAgentIcon size={15} color="#fff" />
                }
              </div>

              <div style={msg.role === 'user' ? styles.bubbleUser : styles.bubbleAgent}>
                {msg.isGreeting ? (
                  <div key={msg.content} style={{ whiteSpace: 'pre-line', animation: 'greetingFade 0.6s ease' }}>
                    {msg.content}
                  </div>
                ) : (
                  <div style={{ whiteSpace: 'pre-line' }}>{msg.content}</div>
                )}

                {msg.orderStatus && <OrderTrackingCard data={msg.orderStatus} wa={wa} />}

                {msg.products && msg.products.length > 0 && (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '12px', marginTop: '12px', width: '100%' }}>
                    {msg.products.map((prod, pIdx) => (
                      <div key={pIdx} style={{ backgroundColor: wa.productCardBg, border: `1px solid ${wa.productCardBorder}`, borderRadius: '8px', padding: '10px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                        <img src={prod.image_url} alt="" style={{ width: '100%', height: '110px', objectFit: 'cover', borderRadius: '4px', marginBottom: '8px' }} />
                        <p style={{ fontSize: '12px', fontWeight: 'bold', margin: '0 0 4px 0', color: wa.bubbleAgentText, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{prod.name}</p>
                        <p style={{ fontSize: '13px', fontWeight: '900', color: '#60a5fa', margin: '0 0 8px 0' }}>LKR {parseFloat(prod.price || 0).toLocaleString()}</p>

                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px', marginBottom: '8px' }}>
                          <span style={{ fontSize: '10px', color: wa.textFaint, fontWeight: '600' }}>Qty</span>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <button onClick={() => bumpProductQty(prod.id, -1)} style={styles.qtyStepperBtn}>−</button>
                            <span style={{ minWidth: '16px', textAlign: 'center', fontWeight: 'bold', fontSize: '12px', color: wa.bubbleAgentText }}>{getProductQty(prod.id)}</span>
                            <button onClick={() => bumpProductQty(prod.id, 1)} style={styles.qtyStepperBtn}>+</button>
                          </div>
                        </div>

                        <button onClick={() => addToCart(prod, getProductQty(prod.id))} style={{ width: '100%', backgroundColor: '#eab308', border: 'none', color: '#000', padding: '6px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '11px' }}>
                          🛒 Add
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px', position: 'relative', zIndex: 1 }}>
              <div style={{
                width: '30px', height: '30px', borderRadius: '50%', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: wa.accent
              }}>
                <ShoppingAgentIcon size={15} color="#fff" />
              </div>
              <div style={{ fontSize: '12px', color: '#8696a0', fontStyle: 'italic', paddingLeft: '4px' }}>{loadingLabel}</div>
            </div>
          )}
        </div>

        <div style={styles.inputDeckContainer}>
          <div style={styles.searchBarWrapper}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder={isListening ? "🎙️ Listening..." : "Type a message or tap the mic to speak..."}
              style={styles.inlineInput}
              disabled={isListening}
            />

            <select value={selectedDialect} onChange={(e) => setSelectedDialect(e.target.value)} style={styles.inlineSelect} disabled={isListening}>
              <option value="en-US">English (US)</option>
              <option value="si-LK">Sinhala (සිංහල)</option>
              <option value="ta-LK">Tamil (தமிழ்)</option>
            </select>

            <button
              onClick={toggleVoiceTranscription}
              title="Toggle Voice Input Profile"
              style={{
                ...styles.micButton,
                backgroundColor: isListening ? '#ef4444' : 'transparent',
                color: isListening ? '#fff' : wa.inlineText,
                boxShadow: isListening ? '0 0 12px rgba(239,68,68,0.4)' : 'none',
              }}
            >
              {isListening ? <MicOffIcon size={18} color="#fff" /> : <MicIcon size={18} color={wa.inlineText} />}
            </button>

            <button
              onClick={() => handleSendMessage()}
              style={{ ...styles.sendButton, padding: 0, width: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              disabled={isListening}
              title="Send"
            >
              <SendIcon size={16} color="#fff" />
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ChatPage />} />
      <Route path="/payment" element={<PaymentPage />} />
      <Route path="/track" element={<TrackPage />} />
    </Routes>
  );
}