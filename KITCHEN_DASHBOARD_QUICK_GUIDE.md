# Kitchen Dashboard - Quick Start Guide

## 🎯 Overview
The Kitchen Dashboard is a complete management system for kitchen staff to track and manage all restaurant orders in real-time with an intuitive split-view design.

## 🚀 Access
**URL**: `/kitchen` or click "Kitchen Dashboard" from owner dashboard

## 📊 Dashboard Layout

### **Split-View Design**
```
┌─────────────────────────────────────────────┐
│ Header: Stats + Time + Controls            │
├──────────────┬──────────────────────────────┤
│              │                              │
│  Orders      │  Order Details Panel         │
│  List        │                              │
│  (Left)      │  • Order Info                │
│              │  • Status Controls           │
│  Compact     │  • Items Table               │
│  Cards       │                              │
│              │                              │
└──────────────┴──────────────────────────────┘
```

### Header Stats Bar
- **New** (Orange): Orders waiting to be started
- **Preparing** (Blue): Orders currently being cooked
- **Ready** (Green): Orders ready to serve
- **Done** (Purple): Completed orders today

### Left Sidebar - Orders List
- Compact order cards showing:
  - Order number (e.g., #ORD123)
  - Table number
  - Number of items
  - Time elapsed (color-coded)
- Filter tabs: All Orders | New | Preparing | Ready
- Click any order to see full details

### Right Panel - Order Details
- Full order information
- Large, clear status action buttons
- Complete items list with quantities
- Special notes highlighted

## 🎮 How to Use

### Step-by-Step Workflow

#### 1️⃣ **New Order Arrives**
- Order appears in left sidebar with orange border
- Sound notification plays
- Click on the order to see details

#### 2️⃣ **View Order Details**
- Order details appear in right panel
- See all items with quantities
- Check for special notes (in orange)

#### 3️⃣ **Start Preparing**
- Click **"START PREPARING"** button
- Order border turns blue
- Customer sees "Being prepared"

#### 4️⃣ **Mark as Ready**
- Click **"MARK READY"** button when cooked
- Order border turns green
- Customer sees "Order ready!"

#### 5️⃣ **Complete Order**
- Click **"MARK SERVED"** button when delivered
- Order border turns purple
- Order moves to completed

### Filter Orders
Use the filter tabs in sidebar:
- **All Orders**: Show all active orders
- **New**: Show only pending orders
- **Preparing**: Show only orders being cooked
- **Ready**: Show only ready orders

## 🎨 Visual Indicators

### Order Card Colors
- **Orange left border**: New/Pending
- **Blue left border**: Preparing
- **Green left border**: Ready
- **Purple left border**: Completed

### Time Elapsed Badges
- **Green badge** (< 10 min): Fresh, normal priority
- **Yellow badge** (10-20 min): Attention needed
- **Red badge** (> 20 min): Urgent!

## 🔔 Notifications

### Sound Alerts
- Plays automatically for new orders
- Double beep sound pattern
- Helps ensure no order is missed

### Toast Messages
- **Green**: Success (status updated)
- **Blue**: Info (new order received)
- **Red**: Error (something failed)

## 💡 Best Practices

### ✅ DO:
1. **Keep sidebar open** - Monitor all incoming orders
2. **Click orders immediately** - Review details when they arrive
3. **Update status promptly** - Keep workflow moving
4. **Check special notes** - Look for orange text in items
5. **Watch time badges** - Prioritize red/yellow orders
6. **Use filters** - Focus on specific status when busy

### ❌ DON'T:
1. Don't leave orders in wrong status
2. Don't miss special preparation notes
3. Don't ignore urgent time warnings (red badges)
4. Don't close dashboard during service hours

## 🖱️ User Interface Tips

### Compact Design Benefits:
- **See more orders at once** - No scrolling needed for most shifts
- **Larger clickable areas** - Easy to tap on touch screens
- **Clear visual hierarchy** - Important info stands out
- **Less clutter** - Focus on what matters

### Keyboard/Touch:
- Click/tap any order card to view details
- Large buttons for easy touch on tablets
- Responsive design works on any screen

## 📱 Customer Integration

When you update order status:
- **Pending → Preparing**: Customer sees "🔥 Your order is being prepared"
- **Preparing → Ready**: Customer sees "✅ Your order is ready!"
- **Ready → Completed**: Order marked as delivered

Real-time sync means customers see updates immediately!

## 🆘 Troubleshooting

**Orders not appearing?**
- Check internet connection
- Refresh page
- Verify you're logged in

**Can't update status?**
- Check if you have permission
- Verify internet connection
- Try refreshing page

**Sound not working?**
- Allow audio in browser
- Check device volume
- Browser may block auto-play

## 📞 Support
Contact restaurant owner or system admin for:
- Access issues
- Technical problems
- Feature requests
- Training

---

**Remember**: The kitchen dashboard directly affects customer experience. 
Keep orders moving and statuses accurate! 🍳👨‍🍳

