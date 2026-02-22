## ENV
Can be used on systems with glibc versions higher or equal than 2.14

## Build
```bash
pyinstaller --onefile --clean --strip --add-data "default.yaml:." --name reget reget.py
```

## arguments
--pattern
    email
    date
    mac
    ipv4
    ipv6
    ...
--highlight
--stat
--unique
--output
    json
--timeout

## example
```bash
reget --pattern email,phone --stat ./user.log
```