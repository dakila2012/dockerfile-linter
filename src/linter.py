from typing import List, Tuple, Optional
import re
import json
def get_instructions(content: str) -> List[Tuple[int, Optional[str], str]]:
    lines = content.splitlines()
    instructions = []
    escape_char = '\\'
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            if stripped.startswith('# escape='):
                esc_part = stripped[9:].strip()
                if esc_part and esc_part[0] in ('\\', '`'):
                    escape_char = esc_part[0]
            i += 1
            continue
        match = re.match(r'^\s*([A-Z]+)\s*(.*)$', line, re.I)
        if not match:
            instructions.append((i + 1, None, stripped))
            i += 1
            continue
        instruction = match.group(1).upper()
        args_str = match.group(2)
        line_num = i + 1
        i += 1
        while i < len(lines) and lines[i].rstrip().endswith(escape_char):
            cont_line = lines[i]
            cont_arg = cont_line.rstrip()[:-1].lstrip()
            args_str += ' ' + cont_arg
            i += 1
        instructions.append((line_num, instruction, args_str))
    return instructions
def lint(content: str) -> List[Tuple[int, str]]:
    instructions = get_instructions(content)
    issues: List[Tuple[int, str]] = []
    from_count = 0
    has_cmd = False
    has_entrypoint = False
    known_instructions = {
        'FROM', 'RUN', 'CMD', 'ENTRYPOINT', 'LABEL', 'COPY', 'ADD', 'USER', 'SHELL',
        'WORKDIR', 'ENV', 'ARG', 'EXPOSE', 'VOLUME', 'ONBUILD', 'STOPSIGNAL',
        'HEALTHCHECK', 'MAINTAINER'
    }
    for line_num, instruction, args_str in instructions:
        if instruction is None:
            issues.append((line_num, 'Invalid instruction syntax'))
            continue
        if instruction not in known_instructions:
            issues.append((line_num, f'Unknown Dockerfile instruction: {instruction}'))
        # JSON exec form syntax check
        if instruction in ('CMD', 'ENTRYPOINT', 'RUN'):
            stripped_args = args_str.strip()
            if stripped_args.startswith('['):
                try:
                    parsed = json.loads(stripped_args)
                    if not isinstance(parsed, list) or not all(isinstance(arg, str) for arg in parsed):
                        issues.append((line_num, f'Invalid exec form for {instruction}: must be JSON array of strings'))
                except json.JSONDecodeError:
                    issues.append((line_num, f'Malformed JSON array for {instruction} exec form'))
        if instruction == 'FROM':
            from_count += 1
            if re.search(r':latest\b', args_str):
                issues.append((line_num, 'Avoid ":latest" tag; pin to a specific version for reproducibility'))
        elif instruction == 'ADD':
            issues.append((line_num, 'Avoid ADD; use COPY for files, ADD only for remote URLs'))
        elif instruction == 'MAINTAINER':
            issues.append((line_num, 'MAINTAINER deprecated; use LABEL maintainer="..."'))
        elif instruction == 'RUN':
            if re.search(r'\bsudo\b', args_str, re.I):
                issues.append((line_num, 'Avoid sudo in RUN commands'))
            # apt
            apt_cmd = re.search(r'apt-get\s+(?:update|upgrade|install|dist-upgrade)', args_str)
            apt_clean = bool(re.search(r'(?:apt-get\s+(?:clean|autoclean)|rm\s+-rf\s+/var/lib/(?:apt/lists/|dpkg))', args_str))
            if apt_cmd and not apt_clean:
                issues.append((line_num, 'Clean apt cache after apt-get: "&& apt-get clean && rm -rf /var/lib/apt/lists/*"'))
            # yum/dnf
            yum_cmd = re.search(r'\b(?:yum|dnf)\s+(?:update|upgrade|install)', args_str, re.I)
            yum_clean = bool(re.search(r'\b(?:yum|dnf)\s+clean\s+all\b', args_str, re.I))
            if yum_cmd and not yum_clean:
                issues.append((line_num, 'Clean yum/dnf cache after commands: "&& yum clean all"'))
            # apk
            if re.search(r'\bapk\s+add\b', args_str, re.I):
                if not re.search(r'--no-cache', args_str):
                    issues.append((line_num, 'Use --no-cache with apk add'))
        elif instruction in ('CMD', 'ENTRYPOINT'):
            if instruction == 'CMD':
                has_cmd = True
            else:
                has_entrypoint = True
            if not args_str.strip().startswith('['):
                issues.append((line_num, f'Use exec form (JSON array) for {instruction}'))
        elif instruction == 'USER':
            if re.match(r'^\s*root\b', args_str, re.I):
                issues.append((line_num, 'Avoid running as root; use a non-root user'))
        elif instruction == 'SHELL':
            if re.match(r'^\s*\[\s*"/bin/sh"\s*,\s*"-c"\s*\]\s*$', args_str.strip()):
                issues.append((line_num, 'Avoid unnecessary SHELL ["/bin/sh", "-c"]; it is default'))
    if from_count == 0:
        issues.append((0, 'Missing FROM instruction'))
    if not (has_cmd or has_entrypoint):
        issues.append((0, 'Missing CMD or ENTRYPOINT'))
    return issues
