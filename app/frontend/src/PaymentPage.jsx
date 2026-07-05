import React, { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';

// Full-page "Pay Now" step. In this demo flow there's no real payment
// gateway wired up yet — Pay Now simulates a short processing delay and
// then marks the order as paid, so the UX (payment page -> confirmation ->
// track order) can be built and tested end-to-end before a real gateway
// is connected.
export default function PaymentPage() {
    const location = useLocation();
    const navigate = useNavigate();
    const checkoutData = location.state?.checkoutData;

    const [status, setStatus] = useState('idle'); // idle | processing | paid

    if (!checkoutData) {
        return (
            <div style={styles.page}>
                <div style={styles.card}>
                    <h2 style={styles.title}>No active checkout</h2>
                    <p style={styles.subtle}>
                        We couldn't find an active order to pay for. Add something to your cart and hit
                        Buy Now from the chat page first.
                    </p>
                    <Link to="/" style={styles.primaryBtnLink}>← Back to chat</Link>
                </div>
            </div>
        );
    }

    const { order_ref, summary = {} } = checkoutData;
    const currency = summary.currency || 'LKR';
    const fmt = (n) => (n || n === 0) ? Number(n).toLocaleString() : '—';

    const handlePayNow = () => {
        setStatus('processing');
        // Simulated gateway delay — replace with a real payment call later.
        setTimeout(() => setStatus('paid'), 1400);
    };

    const handleTrackOrder = () => {
        navigate('/track', { state: { orderRef: order_ref } });
    };

    return (
        <div style={styles.page}>
            <div style={styles.card}>
                <div style={styles.badge}>🧾 Order Summary</div>
                <h2 style={styles.title}>Order {order_ref || ''}</h2>

                {status !== 'paid' && (
                    <p style={styles.subtle}>Review your order and complete payment to continue.</p>
                )}

                <div style={styles.summaryBox}>
                    <div style={styles.summaryLine}><span>Items total</span><span>{currency} {fmt(summary.items_total)}</span></div>
                    <div style={styles.summaryLine}><span>Delivery fee</span><span>{currency} {fmt(summary.delivery_fee)}</span></div>
                    <div style={styles.summaryLine}><span>Add-ons</span><span>{currency} {fmt(summary.addons_total)}</span></div>
                    <div style={{ ...styles.summaryLine, ...styles.grandTotalLine }}>
                        <span>Grand total</span><span>{currency} {fmt(summary.grand_total)}</span>
                    </div>
                </div>

                {status === 'idle' && (
                    <button style={styles.payBtn} onClick={handlePayNow}>
                        💳 Pay Now
                    </button>
                )}

                {status === 'processing' && (
                    <button style={{ ...styles.payBtn, opacity: 0.7, cursor: 'default' }} disabled>
                        ⏳ Processing payment…
                    </button>
                )}

                {status === 'paid' && (
                    <>
                        <div style={styles.successBox}>✅ Payment successful!</div>
                        <button style={styles.trackBtn} onClick={handleTrackOrder}>
                            📦 Track My Order
                        </button>
                    </>
                )}

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
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#0f172a',
        color: '#f8fafc',
        fontFamily: 'system-ui, sans-serif',
        padding: '24px',
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
    badge: {
        display: 'inline-block',
        fontSize: '11px',
        fontWeight: 'bold',
        padding: '4px 10px',
        borderRadius: '999px',
        backgroundColor: '#172554',
        color: '#60a5fa',
        marginBottom: '12px',
    },
    title: { margin: '0 0 8px 0', fontSize: '20px', fontWeight: 800 },
    subtle: { fontSize: '13px', color: '#94a3b8', margin: '0 0 20px 0', lineHeight: 1.5 },
    summaryBox: {
        backgroundColor: '#0f172a',
        border: '1px solid #334155',
        borderRadius: '10px',
        padding: '14px',
        marginBottom: '20px',
    },
    summaryLine: {
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '13px',
        color: '#cbd5e1',
        padding: '4px 0',
    },
    grandTotalLine: {
        borderTop: '1px solid #334155',
        marginTop: '6px',
        paddingTop: '10px',
        fontWeight: 800,
        fontSize: '15px',
        color: '#eab308',
    },
    payBtn: {
        width: '100%',
        border: 'none',
        borderRadius: '10px',
        padding: '14px',
        fontWeight: 800,
        fontSize: '14px',
        color: '#000',
        backgroundColor: '#eab308',
        cursor: 'pointer',
        marginBottom: '16px',
    },
    successBox: {
        backgroundColor: '#052e1e',
        border: '1px solid #14532d',
        color: '#4ade80',
        borderRadius: '10px',
        padding: '12px',
        textAlign: 'center',
        fontWeight: 700,
        fontSize: '14px',
        marginBottom: '14px',
    },
    trackBtn: {
        width: '100%',
        border: 'none',
        borderRadius: '10px',
        padding: '13px',
        fontWeight: 800,
        fontSize: '14px',
        color: '#000',
        backgroundColor: '#00a884',
        cursor: 'pointer',
        marginBottom: '16px',
    },
    backLink: { fontSize: '12px', color: '#94a3b8', textDecoration: 'none' },
    primaryBtnLink: {
        display: 'inline-block',
        marginTop: '12px',
        fontSize: '13px',
        fontWeight: 700,
        color: '#00a884',
        textDecoration: 'none',
    },
};