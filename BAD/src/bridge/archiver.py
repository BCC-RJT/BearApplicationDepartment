import discord
import os
import json
import aiohttp
from datetime import datetime
from src import db

# Base archive directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARCHIVE_ROOT = os.path.join(PROJECT_ROOT, 'data', 'archives')

async def archive_ticket(channel: discord.TextChannel):
    """
    Archives a ticket channel by saving its history and attachments.
    Returns the absolute path to the archive directory.
    """
    # 1. Get Ticket Details from DB
    ticket_data = db.get_ticket(channel.id)
    ticket_id = ticket_data['id'] if ticket_data else "unknown"
    
    # 2. Create Directory: data/archives/YYYY/MM/ticket_id/
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    
    archive_dir = os.path.join(ARCHIVE_ROOT, year, month, str(ticket_id))
    attachments_dir = os.path.join(archive_dir, "attachments")
    os.makedirs(attachments_dir, exist_ok=True)
    
    # 3. Fetch History
    messages = []
    
    async for msg in channel.history(limit=None, oldest_first=True):
        msg_data = {
            "id": msg.id,
            "timestamp": msg.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "author_id": msg.author.id,
            "author_name": msg.author.display_name,
            "content": msg.content,
            "attachments": []
        }
        
        # Download Attachments
        if msg.attachments:
            for att in msg.attachments:
                # Sanitize filename
                safe_filename = f"{msg.id}_{att.filename}"
                local_path = os.path.join(attachments_dir, safe_filename)
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(att.url) as resp:
                            if resp.status == 200:
                                with open(local_path, 'wb') as f:
                                    f.write(await resp.read())
                                    
                    msg_data["attachments"].append({
                        "original_url": att.url,
                        "filename": att.filename,
                        "local_path": f"attachments/{safe_filename}",
                        "size": att.size
                    })
                except Exception as e:
                    print(f"❌ Failed to download attachment {att.url}: {e}")
                    msg_data["attachments"].append({
                        "original_url": att.url,
                        "error": str(e)
                    })
        
        messages.append(msg_data)
        
    # 4. Save JSON Transcript
    transcript_data = {
        "meta": {
            "ticket_id": ticket_id,
            "channel_id": channel.id,
            "channel_name": channel.name,
            "archived_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "title": ticket_data.get('title', 'No Title') if ticket_data else 'No Title',
            "description": ticket_data.get('description', '') if ticket_data else ''
        },
        "messages": messages
    }
    
    json_path = os.path.join(archive_dir, "transcript.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
    # 5. Save HTML Transcript (Simple Viewer)
    html_content = generate_html_transcript(transcript_data)
    html_path = os.path.join(archive_dir, "transcript.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    # 6. Update DB
    db.update_archive_path(channel.id, archive_dir)
    print(f"✅ Archived ticket {ticket_id} to {archive_dir}")
    
    return archive_dir

def generate_html_transcript(data):
    """Generates a simple HTML view of the transcript."""
    meta = data['meta']
    messages = data['messages']
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ticket #{meta['ticket_id']} - Archive</title>
        <style>
            body {{ font-family: sans-serif; background: #36393f; color: #dcddde; padding: 20px; }}
            .header {{ border-bottom: 1px solid #72767d; padding-bottom: 10px; margin-bottom: 20px; }}
            .message {{ margin-bottom: 15px; padding: 10px; border-radius: 5px; background: #2f3136; }}
            .author {{ font-weight: bold; color: #fff; }}
            .time {{ font-size: 0.8em; color: #72767d; margin-left: 10px; }}
            .content {{ margin-top: 5px; white-space: pre-wrap; }}
            .attachment {{ margin-top: 10px; }}
            a {{ color: #00b0f4; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Ticket #{meta['ticket_id']}: {meta['title']}</h1>
            <p><strong>Channel:</strong> {meta['channel_name']}</p>
            <p><strong>Archived:</strong> {meta['archived_at']}</p>
            <p><strong>Description:</strong> {meta['description']}</p>
        </div>
        <div class="messages">
    """
    
    for msg in messages:
        attachments_html = ""
        for att in msg['attachments']:
             if 'local_path' in att:
                 attachments_html += f'<div class="attachment">📎 <a href="{att["local_path"]}" target="_blank">{att["filename"]}</a></div>'
             else:
                 attachments_html += f'<div class="attachment">⚠️ Failed to load: {att["original_url"]}</div>'
                 
        html += f"""
            <div class="message">
                <span class="author">{msg['author_name']}</span>
                <span class="time">{msg['timestamp']}</span>
                <div class="content">{msg['content']}</div>
                {attachments_html}
            </div>
        """
        
    html += """
        </div>
    </body>
    </html>
    """
    return html

async def restore_ticket_from_archive(interaction, ticket_id):
    """
    Restores an archived ticket to a new channel.
    """
    # 1. Look up Archive Path
    path = db.get_archive_path(ticket_id)
    if not path or not os.path.exists(path):
        return f"❌ Archive not found for ticket {ticket_id}."
        
    json_path = os.path.join(path, "transcript.json")
    if not os.path.exists(json_path):
        return f"❌ Transcript file missing at {json_path}."
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    meta = data['meta']
    messages = data['messages']
    
    guild = interaction.guild
    
    # 2. Create Channel
    base_name = meta.get('channel_name', f"ticket-{ticket_id}-restored")
    new_name = f"{base_name}-restored"
    
    # Find active category
    category = discord.utils.get(guild.categories, name="📨 Incoming Tickets") or \
               discord.utils.get(guild.categories, name="Tickets Inbox")
               
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    channel = await guild.create_text_channel(new_name, category=category, overwrites=overwrites)
    
    # 3. Replay History
    await channel.send(f"🔄 **Restoring Ticket History (ID: {ticket_id})**\nArchived on: {meta['archived_at']}")
    
    # We can use webhooks to impersonate, but simple bot playback is safer/easier permission-wise
    # But bot playback loses original timestamps (though we can put them in text)
    
    for msg in messages:
        timestamp = msg['timestamp']
        author = msg['author_name']
        content = msg['content']
        
        # Prepare Attachments
        files = []
        if msg['attachments']:
            for att in msg['attachments']:
                local_file = os.path.join(path, att['local_path'])
                if os.path.exists(local_file):
                    files.append(discord.File(local_file))
        
        # Format message
        # "[2023-01-01 12:00] User: content"
        formatted_content = f"**{author}** `[{timestamp}]`:\n{content}"
        
        try:
            await channel.send(content=formatted_content, files=files)
        except Exception as e:
            await channel.send(f"⚠️ Failed to restore a message: {e}")
            
    await channel.send("✅ **Restoration Complete.** You can now continue the conversation.")
    
    # 4. Update DB status
    # We might need to map the old ticket ID to the NEW channel ID?
    # Or just treat this as a "New" ticket with history?
    # User said "restore any ticket". 
    # If we want to maintain the SAME ticket_id record, we update the channel_id in DB?
    # PROBABLY NOT A GOOD IDEA to update channel_id as it breaks history of the old channel?
    # But current system (db.py) maps status by channel_id (mostly).
    # Since existing system uses `tickets table` keyed by `id` effectively (pk), but looked up by channel_id.
    
    # Let's create a NEW DB record for the restored ticket, linked to the old one?
    # Or just update the old record with the new channel ID and status=active.
    # Updating seems cleaner for "Restoring" the same entity.
    
    # Update DB with new channel ID
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("UPDATE tickets SET channel_id = ?, status = 'active' WHERE id = ?", (str(channel.id), ticket_id))
    conn.commit()
    conn.close()
    
    return channel
