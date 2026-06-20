"""GNU Screen integration helpers for systemd services.

Running a service inside GNU Screen under systemd requires the *non-forking*
detached mode so the service manager can keep tracking the live process:

* ``screen -DmS`` (capital ``-D``) starts screen detached **without forking** a
  new process. The command stays in the foreground and exits when the session
  terminates, which is exactly what ``Type=simple`` expects.
* ``screen -dmS`` (lowercase ``-d``) forks into the background, so systemd sees
  the ``ExecStart`` process exit immediately and tears the session down. This is
  the bug this module fixes.

A matching ``ExecStop`` (``screen -S <session> -X quit``) lets ``systemctl stop``
terminate the session cleanly.

References:
    * GNU Screen manual, "Invoking Screen" (``-d -m`` vs ``-D -m``):
      https://www.gnu.org/software/screen/manual/html_node/Invoking-Screen.html
    * Arch Wiki, "GNU Screen # Autostart with systemd".
    * systemd.service(5), ``Type=simple``.
"""

from typing import List, Optional
import os
import re

SCREEN_BIN = "/usr/bin/screen"

# Combined flags that take the session name as their following argument.
_SESSION_FLAGS = ("-DmS", "-dmS", "-S")

# Matches a standalone legacy forking flag (bounded by whitespace or string
# edges) so only the flag token is rewritten and surrounding text — including
# significant whitespace inside quoted arguments — is preserved verbatim.
_LEGACY_FLAG_RE = re.compile(r"(?<!\S)-dmS(?!\S)")


def _screen_program_index(tokens: List[str]) -> Optional[int]:
    """Return the index of the ``screen`` binary when it is the launched program.

    Returns ``None`` unless the first token's basename is ``screen``, so a
    command that merely passes ``screen`` as an argument (e.g. ``cat screen``)
    is not misclassified as a screen service.
    """
    if tokens and os.path.basename(tokens[0]) == "screen":
        return 0
    return None


def screen_session_name(service_name: str) -> str:
    """Return the canonical GNU Screen session name for a service.

    Used by both the GUI and the CLI so a given service always maps to the same
    session name.
    """
    return f"service_{service_name}"


def build_screen_command(session_name: str, base_command: str) -> str:
    """Build an ``ExecStart`` command that runs ``base_command`` inside a
    foreground (non-forking) GNU Screen session, suitable for ``Type=simple``.

    Uses ``-DmS`` (capital ``-D``: detached but does not fork) per the GNU Screen
    manual, with an absolute path to the ``screen`` binary.
    """
    return f"{SCREEN_BIN} -DmS {session_name} {base_command}"


def screen_stop_command(session_name: str) -> str:
    """Return the ``ExecStop`` command that cleanly quits the screen session."""
    return f"{SCREEN_BIN} -S {session_name} -X quit"


def is_screen_command(exec_start: str) -> bool:
    """Return ``True`` if ``exec_start`` launches a *named* GNU Screen session.

    Both conditions must hold so the screen handling only triggers for commands
    this tool genuinely treats as screen services:

    * ``screen`` is the launched program (the first token's basename), not just
      an argument that happens to be named ``screen``; and
    * a session name can be parsed from a ``-DmS``/``-dmS``/``-S`` flag.

    A bare ``screen mycmd`` or a forking ``screen -dm mycmd`` (no named session)
    is therefore rendered as an ordinary service rather than being silently
    forced to ``Type=simple`` — the screen handling can only correct a command
    that actually names a session.
    """
    if _screen_program_index(exec_start.split()) is None:
        return False
    return screen_session_from_command(exec_start) is not None


def screen_session_from_command(exec_start: str) -> Optional[str]:
    """Extract the session name from a ``screen ... -DmS <session> ...`` command.

    The search is anchored to the ``screen`` program token and only considers
    the tokens that follow it, so a stray ``-S``/``-DmS`` appearing earlier in a
    wrapper command cannot be mistaken for the session. Option-like tokens
    (starting with ``-``) are skipped, and ``None`` is returned when no session
    name can be found.
    """
    tokens = exec_start.split()
    start = _screen_program_index(tokens)
    if start is None:
        return None
    for index in range(start + 1, len(tokens) - 1):
        if tokens[index] in _SESSION_FLAGS:
            candidate = tokens[index + 1]
            if not candidate.startswith("-"):
                return candidate
    return None


def normalize_screen_command(exec_start: str) -> str:
    """Rewrite a legacy forking ``-dmS`` flag to the non-forking ``-DmS`` form.

    Only the standalone ``-dmS`` flag token is rewritten (via a regex with
    whitespace boundaries); every other byte — including significant whitespace
    inside quoted arguments — is preserved exactly. This repairs ``ExecStart``
    strings saved by older versions at render time, without a data migration and
    without altering the command the unit actually runs.
    """
    return _LEGACY_FLAG_RE.sub("-DmS", exec_start)
