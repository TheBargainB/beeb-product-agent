# WhatsApp Formatting Guide

## 🛠️ **Problem Solved**

Your assistant was responding with markdown formatting (`**bold**`, `# headers`, etc.) which looks ugly in WhatsApp since WhatsApp doesn't render markdown properly.

**Before Fix:**
```
**Recipe for Hummus**

## Ingredients:
- **2 cups** chickpeas
- **1/4 cup** tahini

## Instructions:
1. Blend ingredients
2. Add water if needed
```

**After Fix (WhatsApp):**
```
🍽️ *Recipe for Hummus*

📌 *Ingredients*:
• *2 cups* chickpeas
• *1/4 cup* tahini

📌 *Instructions*:
• Blend ingredients
• Add water if needed
```

## 🚀 **How to Enable WhatsApp Formatting**

### For Your WhatsApp Integration

Simply add `source: "whatsapp"` to your configuration:

```javascript
const config = {
    configurable: {
        user_id: "user123",
        thread_id: "conversation456",
        source: "whatsapp"  // 👈 This enables WhatsApp formatting
    }
}
```

### For Testing

```python
# Test with WhatsApp formatting
config = {
    "configurable": {
        "user_id": "test_user",
        "thread_id": "test_thread",
        "source": "whatsapp"
    }
}

# Test without formatting (web/telegram)
config = {
    "configurable": {
        "user_id": "test_user", 
        "thread_id": "test_thread",
        "source": "general"  // or "web" or "telegram"
    }
}
```

## 🔄 **What Gets Converted**

| Markdown | WhatsApp Friendly |
|----------|-------------------|
| `**bold**` | `*bold*` |
| `# Header` | `🔥 *Header*` |
| `## Subheader` | `📌 *Subheader*` |
| `- List item` | `• List item` |
| `**INGREDIENTS**:` | `*🥘 INGREDIENTS*:` |
| `**INSTRUCTIONS**:` | `*👨‍🍳 INSTRUCTIONS*:` |
| `**RECIPE**:` | `*🍽️ RECIPE*:` |

## 🧪 **Testing the Fix**

Run the test script to verify everything works:

```bash
python test_whatsapp_formatting.py
```

This will show you:
- ✅ Before/after formatting examples
- ✅ Agent responses with and without formatting
- ✅ Specific conversion tests

## 🎯 **Content-Aware Formatting**

The system automatically detects content type and adds relevant emojis:

- **Recipes**: 🥘 🍽️ 👨‍🍳 ⏱️ 🍿
- **Grocery Lists**: 🛒 💰 🏪
- **Meal Plans**: 🌅 🌞 🌙 🍿
- **General**: 🔥 📌 💡

## 💬 **For Your WhatsApp Service**

Update your WhatsApp integration to pass the source parameter:

```javascript
// In your WhatsApp AI service
const aiResponse = await fetch('/api/ai/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: userMessage,
        config: {
            configurable: {
                user_id: userId,
                thread_id: threadId,
                source: "whatsapp"  // 👈 Add this
            }
        }
    })
});
```

## ✅ **Benefits**

- **Clean WhatsApp messages**: No more ugly markdown
- **Visual appeal**: Relevant emojis and proper formatting
- **Platform-specific**: Only applies to WhatsApp, other platforms unchanged
- **Automatic**: No manual formatting needed
- **Backward compatible**: Existing code continues to work

## 🔧 **Troubleshooting**

**Q: Formatting not being applied?**
- Check that `source: "whatsapp"` is in your config
- Verify the config reaches the agent properly

**Q: Still seeing markdown?**
- The source parameter might not be set correctly
- Check the test script to verify the formatter works

**Q: Want to customize formatting?**
- Edit `src/agent/whatsapp_formatter.py`
- Modify the emoji mappings or formatting rules
- Test with `test_whatsapp_formatting.py`

---

**🎉 Result: Clean, professional-looking responses in WhatsApp with proper formatting and contextual emojis!** 