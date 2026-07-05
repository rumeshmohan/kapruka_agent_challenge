import React from 'react';

// Package / tracking icon for the "Track my order" quick action & card header
const PackageIcon = ({ size = 16, color = '#fff' }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3.5 7.5L12 3l8.5 4.5v9L12 21l-8.5-4.5v-9z" stroke={color} strokeWidth="1.6" strokeLinejoin="round" fill="none" />
        <path d="M3.5 7.5L12 12l8.5-4.5" stroke={color} strokeWidth="1.6" strokeLinejoin="round" fill="none" />
        <path d="M12 12v9" stroke={color} strokeWidth="1.6" strokeLinecap="round" />
    </svg>
);

const CheckCircleIcon = ({ size = 14, color = '#fff' }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" fill={color} />
        <path d="M7.5 12.5l3 3 6-6.5" stroke="#0f172a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
);

// Canonical delivery journey stages used to render the tracking stepper.
// We map whatever status string the MCP tool returns onto the closest
// stage here, so the UI stays consistent even if wording varies slightly
// (e.g. "Out for Delivery" vs "out_for_delivery" vs "Dispatched").
const TRACKING_STAGES = ['Placed', 'Packed', 'Shipped', 'Out for Delivery', 'Delivered'];

const normalizeStageIndex = (rawStatus) => {
    if (!rawStatus) return 0;
    const s = String(rawStatus).toLowerCase().replace(/[_-]/g, ' ');
    if (s.includes('deliver') && !s.includes('out for')) return 4;
    if (s.includes('out for delivery') || s.includes('dispatch')) return 3;
    if (s.includes('ship') || s.includes('transit')) return 2;
    if (s.includes('pack') || s.includes('process')) return 1;
    if (s.includes('placed') || s.includes('confirm') || s.includes('pending')) return 0;
    return 0;
};

// Renders a tracking card from whatever shape the kapruka_track_order tool
// returns. The backend (logistics_agent.py) parses Kapruka's Markdown
// tracking report into this structured shape before it ever reaches here:
//   order_number, status, eta, total, payment_ref, ordered_date,
//   shipped_date, recipient_name, recipient_address, recipient_phone,
//   greeting, notes, events: [{ timestamp, description }]
// We still normalize defensively (string/array/object) in case the MCP
// tool's return shape ever changes upstream.
const OrderTrackingCard = ({ data, wa }) => {
    if (!data) return null;

    let payload = data;
    if (typeof data === 'string') {
        try { payload = JSON.parse(data); } catch (e) { payload = { raw: data }; }
    }
    if (Array.isArray(payload)) {
        payload = payload[0] || { raw: 'No order data returned.' };
    }
    if (!payload || typeof payload !== 'object') {
        payload = { raw: String(payload) };
    }

    const orderNumber = payload.order_number || payload.orderNumber || payload.id || 'N/A';
    const statusLabel = payload.status || payload.order_status || payload.state || 'Processing';
    const eta = payload.eta || payload.estimated_delivery || payload.estimated_delivery_date || payload.delivery_date;
    const courier = payload.courier || payload.carrier || payload.driver_name;
    const location = payload.current_location || payload.location;
    const events = payload.events || payload.timeline || payload.history;

    // Newer fields parsed from Kapruka's Markdown tracking report
    const total = payload.total;
    const paymentRef = payload.payment_ref;
    const orderedDate = payload.ordered_date;
    const shippedDate = payload.shipped_date;
    const recipientName = payload.recipient_name;
    const recipientAddress = payload.recipient_address;
    const recipientPhone = payload.recipient_phone;
    const greeting = payload.greeting;
    const notes = payload.notes;

    const activeStage = normalizeStageIndex(statusLabel);
    const knownFields = new Set([
        'order_number', 'orderNumber', 'id', 'status', 'order_status', 'state',
        'eta', 'estimated_delivery', 'estimated_delivery_date', 'delivery_date',
        'courier', 'carrier', 'driver_name', 'current_location', 'location',
        'events', 'timeline', 'history',
        'total', 'payment_ref', 'ordered_date', 'shipped_date',
        'recipient_name', 'recipient_address', 'recipient_phone', 'greeting', 'notes',
    ]);
    const extraEntries = Object.entries(payload).filter(([k]) => !knownFields.has(k));

    return (
        <div style={{
            backgroundColor: wa.productCardBg, border: `1px solid ${wa.productCardBorder}`,
            borderRadius: '10px', padding: '14px', marginTop: '12px', width: '100%', maxWidth: '360px'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <PackageIcon size={16} color={wa.accent} />
                <span style={{ fontSize: '12px', fontWeight: 'bold', color: wa.bubbleAgentText }}>Order {orderNumber}</span>
                <span style={{
                    marginLeft: 'auto', fontSize: '10px', fontWeight: 'bold', padding: '3px 8px', borderRadius: '10px',
                    backgroundColor: wa.tagPrefBg, color: wa.tagPrefText, border: `1px solid ${wa.tagPrefBorder}`
                }}>
                    {statusLabel}
                </span>
            </div>

            {/* Stepper */}
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
                {TRACKING_STAGES.map((stage, idx) => (
                    <React.Fragment key={stage}>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: idx === TRACKING_STAGES.length - 1 ? '0 0 auto' : 1 }}>
                            <div style={{
                                width: '18px', height: '18px', borderRadius: '50%',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                backgroundColor: idx <= activeStage ? wa.accent : wa.fieldBg,
                                border: `1px solid ${idx <= activeStage ? wa.accent : wa.fieldBorder}`,
                                flexShrink: 0
                            }}>
                                {idx <= activeStage && <CheckCircleIcon size={12} color="#fff" />}
                            </div>
                            <span style={{ fontSize: '8px', color: idx <= activeStage ? wa.bubbleAgentText : wa.textFaint, marginTop: '4px', textAlign: 'center', maxWidth: '52px' }}>
                                {stage}
                            </span>
                        </div>
                        {idx < TRACKING_STAGES.length - 1 && (
                            <div style={{ flex: 1, height: '2px', backgroundColor: idx < activeStage ? wa.accent : wa.fieldBorder, marginBottom: '14px' }} />
                        )}
                    </React.Fragment>
                ))}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '11px', color: wa.labelText }}>
                {eta && <div><strong>Estimated delivery:</strong> {eta}</div>}
                {courier && <div><strong>Courier:</strong> {courier}</div>}
                {location && <div><strong>Current location:</strong> {location}</div>}
                {total && <div><strong>Order total:</strong> {total}</div>}
                {orderedDate && <div><strong>Ordered:</strong> {orderedDate}</div>}
                {shippedDate && <div><strong>Shipped:</strong> {shippedDate}</div>}
            </div>

            {(recipientName || recipientAddress || recipientPhone) && (
                <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: `1px solid ${wa.cardBorder}`, fontSize: '11px', color: wa.labelText }}>
                    <div style={{ fontWeight: 'bold', marginBottom: '4px', color: wa.bubbleAgentText }}>Delivering to</div>
                    {recipientName && <div>{recipientName}</div>}
                    {recipientAddress && <div style={{ color: wa.textMuted }}>{recipientAddress}</div>}
                    {recipientPhone && <div style={{ color: wa.textMuted }}>{recipientPhone}</div>}
                </div>
            )}

            {greeting && (
                <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: `1px solid ${wa.cardBorder}`, fontSize: '11px', color: wa.labelText, fontStyle: 'italic' }}>
                    "{greeting}"
                </div>
            )}

            {notes && (
                <div style={{ marginTop: '8px', fontSize: '10px', color: wa.textMuted }}>
                    {notes}
                </div>
            )}

            {Array.isArray(events) && events.length > 0 && (
                <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: `1px solid ${wa.cardBorder}` }}>
                    {events.map((ev, i) => (
                        <div key={i} style={{ fontSize: '10px', color: wa.textMuted, marginBottom: '4px' }}>
                            • {typeof ev === 'string' ? ev : (ev.description || ev.status || JSON.stringify(ev))}
                            {ev.timestamp ? ` — ${ev.timestamp}` : ''}
                        </div>
                    ))}
                </div>
            )}

            {extraEntries.length > 0 && (
                <details style={{ marginTop: '10px' }}>
                    <summary style={{ fontSize: '9px', color: wa.textFaint, cursor: 'pointer' }}>More details</summary>
                    <pre style={{ fontSize: '9px', color: wa.textMuted, whiteSpace: 'pre-wrap', marginTop: '6px' }}>
                        {JSON.stringify(Object.fromEntries(extraEntries), null, 2)}
                    </pre>
                </details>
            )}
        </div>
    );
};

export { OrderTrackingCard, PackageIcon, CheckCircleIcon };
export default OrderTrackingCard;