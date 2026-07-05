import React, { useEffect, useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { OrderTrackingCard } from './OrderTrackingCard.jsx';

// Full-page tracking view reached after a (simulated) payment on
// PaymentPage. Reuses the exact same /api/chat tracking path already
// proven to work from the chat sidebar's "Track my order" button, rather
// than a separate untested endpoint, so this page behaves identically to
// the tracking feature that already works today.
const SESSION_ID = "session_user_hf";

export default function TrackPage() {
    const location = useLocation();
    const initialOrderRef = location.state?.orderRef || '';

    const [orderNumberInput, setOrderNumberInput] = useState(initialOrderRef);
    const [orderStatus, setOrderStatus] = useState(null);
    const [statusText, setStatusText] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const fetchTracking = async (orderNumber) => {
        if (!orderNumber) return;
        setLoading(true);
        setError('');
        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: `Where is my order ${orderNumber}?`,
                    session_id: SESSION_ID,
                    cart: [],
                }),
            });
            if (!res.ok) throw new Error('Lookup failed');
            const data = await res.json();
            if (data.order_status) {
                setOrderStatus(data.order_status);
                setStatusText(data.text || '');
            } else {
                setOrderStatus(null);
                setStatusText(data.text || "Couldn't find tracking details for that order.");
            }
        } catch (e) {
            setError("Couldn't reach the tracking service right now. Please try again.");
            setOrderStatus(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (initialOrderRef) {
            fetchTracking(initialOrderRef);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const wa = {
        productCardBg: '#1f2c34', productCardBorder: '#2a3942', bubbleAgentText: '#e9edef',
        accent: '#00a884', fieldBg: '#0f172a', fieldBorder: '#475569', textFaint: '#64748b',
        tagPrefBg: '#172554', tagPrefText: '#60a5fa', tagPrefBorder: '#1e3a8a',
        labelText: '#cbd5e1', textMuted: '#94a3b8', cardBorder: '#334155',
    };

    return (
        <div style={styles.page}>
            <div style={styles.card}>
                <h2 style={styles.title}>📦 Track Your Order</h2>

                <div style={styles.searchRow}>
                    <input
                        type="text"
                        value={orderNumberInput}
                        onChange={(e) => setOrderNumberInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && fetchTracking(orderNumberInput)}
                        placeholder="Enter order number (e.g. VPAY827982BA)"
                        style={styles.input}
                    />
                    <button style={styles.searchBtn} onClick={() => fetchTracking(orderNumberInput)}>
                        Track
                    </button>
                </div>

                {loading && <p style={styles.subtle}>Looking up your order…</p>}
                {error && <p style={styles.error}>{error}</p>}
                {!loading && !error && statusText && !orderStatus && (
                    <p style={styles.subtle}>{statusText}</p>
                )}

                {orderStatus && <OrderTrackingCard data={orderStatus} wa={wa} />}

                <Link to="/" style={styles.backLink}>← Back to chat</Link>
            </div>
        </div>
    );
}

const styles = {
    page: {
        minHeight: '100vh',
        width: '100%',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        backgroundColor: '#0f172a',
        color: '#f8fafc',
        fontFamily: 'system-ui, sans-serif',
        padding: '48px 24px',
        boxSizing: 'border-box',
    },
    card: {
        width: '100%',
        maxWidth: '440px',
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '14px',
        padding: '28px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.35)',
    },
    title: { margin: '0 0 16px 0', fontSize: '20px', fontWeight: 800 },
    searchRow: { display: 'flex', gap: '8px', marginBottom: '16px' },
    input: {
        flex: 1,
        padding: '10px 12px',
        borderRadius: '8px',
        border: '1px solid #475569',
        backgroundColor: '#0f172a',
        color: '#f8fafc',
        fontSize: '13px',
    },
    searchBtn: {
        border: 'none',
        borderRadius: '8px',
        padding: '10px 16px',
        fontWeight: 700,
        fontSize: '13px',
        color: '#000',
        backgroundColor: '#00a884',
        cursor: 'pointer',
    },
    subtle: { fontSize: '13px', color: '#94a3b8' },
    error: { fontSize: '13px', color: '#f87171' },
    backLink: { display: 'inline-block', marginTop: '16px', fontSize: '12px', color: '#94a3b8', textDecoration: 'none' },
};