
import asyncio
import logging

logger = logging.getLogger("SESSION_MANAGER")

class SessionManager:
    def __init__(self):
        # Map channel_id -> session_dict
        # session_dict: { "process": Popen, "command": str, "active": bool }
        self.sessions = {}

    def has_active_session(self, channel_id):
        return channel_id in self.sessions

    async def start_session(self, channel_id, command, output_callback, exit_callback):
        """
        Starts an interactive subprocess.
        output_callback(text): Async function to send text to Discord.
        exit_callback(): Async function to notify Discord of exit.
        """
        if channel_id in self.sessions:
            return False, "Session already active in this channel."

        logger.info(f"Starting session in {channel_id}: {command}")

        try:
            # Use shell=True to allow complex commands/pipes
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self.sessions[channel_id] = {
                "process": process,
                "command": command,
                "active": True
            }

            # Start background readers
            asyncio.create_task(self._monitor_output(process.stdout, channel_id, output_callback))
            asyncio.create_task(self._monitor_output(process.stderr, channel_id, output_callback))
            asyncio.create_task(self._monitor_exit(process, channel_id, exit_callback))

            return True, f"🚀 **Session Started**\nCommand: `{command}`\n*Type messages here to interact.*"
        
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return False, str(e)

    async def send_input(self, channel_id, text):
        """Writes text to the process stdin."""
        session = self.sessions.get(channel_id)
        if not session or not session.get("active"):
            return False
        
        process = session["process"]
        if process.stdin:
            try:
                msg = f"{text}\n"
                process.stdin.write(msg.encode())
                await process.stdin.drain()
                return True
            except Exception as e:
                logger.error(f"Error writing to stdin: {e}")
                return False
        return False

    async def terminate_session(self, channel_id):
        """Force kills the session."""
        session = self.sessions.pop(channel_id, None)
        if session:
            process = session["process"]
            try:
                process.terminate()
                # Give it a moment, then kill if needed
                try:
                    await asyncio.wait_for(process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    process.kill()
            except Exception as e:
                logger.error(f"Error terminating process: {e}")
            return True
        return False

    async def _monitor_output(self, stream, channel_id, callback):
        """Reads stream line-by-line and calls callback."""
        while True:
            try:
                # DEBUG: Log before read
                # logger.debug(f"Reading from stream for {channel_id}...")
                line = await stream.readline()
                # logger.debug(f"Read line: {line}")
                if not line:
                    break
                
                decoded = line.decode().strip()
                if decoded:
                    # Avoid sending empty lines spam
                    await callback(decoded)
            
            except ValueError:
                continue # Ignore binary/encoding errors
            except Exception as e:
                logger.error(f"Stream monitor error: {e}")
                break

    async def _monitor_exit(self, process, channel_id, callback):
        """Waits for process exit and cleans up."""
        await process.wait()
        
        # Cleanup session logic
        if channel_id in self.sessions:
            del self.sessions[channel_id]
        
        await callback(process.returncode)
