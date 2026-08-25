# Multi-NIC Segment Downloader

> **A Windows desktop downloader for direct HTTP/HTTPS links, with English and Vietnamese UI.**
>
> **Status:** Public beta. Use at your own risk and report problems through GitHub Issues.

[English](#english) · [Tiếng Việt](#tiếng-việt)

---

# English

## Overview

Multi-NIC Segment Downloader is a Windows desktop application for downloading files from direct HTTP/HTTPS links. It validates HTTP Range support, divides a file into byte-range segments, and coordinates downloads across selected active IPv4 network interfaces.

The application uses:

- **aria2c.exe** as the download engine.
- **ForceBindIP** to bind the aria2 process to a selected local IPv4 interface/IP.
- **Python + Tkinter** for the desktop UI, queue management, configuration, diagnostics, and English/Vietnamese language switching.

Use this software only for files and services that you are authorized to access. Respect service terms, rate limits, copyright, access controls, and applicable law.

## Features

- English is the default UI language.
- Vietnamese UI is available and can be changed while the app is running.
- Persistent language and settings in local `config.json`.
- Direct HTTP/HTTPS link validation.
- HTTP Range / `206 Partial Content` verification.
- Multi-segment download workflow.
- Active IPv4 network-interface selection.
- Per-interface IP binding through ForceBindIP.
- Download queue and configurable parallel tasks.
- Independent retry handling for failed segments.
- Pause, resume, stop, and remove-from-queue controls.
- Resume support through temporary download files.
- Final merge only after all segments have completed correctly.
- SHA256, SHA1, and MD5 calculation after download completion.
- Built-in diagnostics and dependency management.

## Requirements

- Windows 10 or Windows 11.
- **Python 3.13.1 or newer, 64-bit.**
- **Python 3.13.0 is not supported.** It has a known Tkinter/Tcl issue with Windows virtual environments.
- Python must include the **Tcl/Tk and IDLE** component.
- Internet access on the first run, so Python packages can be installed.
- One or more active IPv4 network interfaces.
- A direct HTTP/HTTPS URL.
- A source server that supports HTTP byte-range requests.
- `aria2c.exe` in the expected application location.
- ForceBindIP installed in the expected `ForceBindIP` folder.

> Multiple network interfaces do **not** guarantee higher download speed. Actual performance depends on routing, ISP capacity, source-server bandwidth, host connection policy, and the quality of each network path.

## Install Python correctly

This app uses Tkinter, which requires Tcl/Tk from the standard Python Windows installer.

1. Download the latest **Python 3.13.x Windows installer (64-bit)** from [python.org](https://www.python.org/downloads/windows/).
2. Do not use Python 3.13.0. Use Python **3.13.1 or newer**.
3. On the first installer screen, select:

   ```text
   Add python.exe to PATH
   ```

4. Select **Customize installation**.
5. In Optional Features, make sure these options are enabled:

   ```text
   pip
   Tcl/Tk and IDLE
   Python Launcher / py launcher
   ```

6. Complete the installation and open a new PowerShell window.
7. Verify Tkinter before running the application:

   ```powershell
   py -3 -c "import tkinter as tk; root=tk.Tk(); root.withdraw(); root.destroy(); print('Tkinter OK')"
   ```

Expected output:

```text
Tkinter OK
```

If this command fails, repair or reinstall Python and ensure **Tcl/Tk and IDLE** is selected.

## Quick start

1. Download this repository as ZIP or clone it with Git.
2. Extract it to a folder where you have write permission, for example:

   ```text
   D:\Tools\MultiNIC-Downloader
   ```

3. Install Python using the instructions above.
4. Install ForceBindIP as described in [ForceBindIP installation](#forcebindip-installation).
5. Double-click `Running.bat`.
6. On first run, `Running.bat` creates a local `.venv` environment and installs packages from `requirements.txt`.
7. Enter a direct link, choose an output folder, select one or more network interfaces, and click **Add to queue**.

If Python was upgraded or repaired after `.venv` was created, delete the local `.venv` folder and run `Running.bat` again:

```powershell
Remove-Item -Recurse -Force .\.venv
```

## How it works

1. The app validates a direct HTTP/HTTPS URL.
2. It checks whether the server supports HTTP Range requests.
3. The download engine divides a file into byte-range segments according to selected interfaces and configured segment settings.
4. ForceBindIP starts/binds aria2 to the selected local interface IP.
5. Failed segments can retry independently.
6. Temporary completed data is retained to support resume after pause or stop.
7. After all segments are valid, the output is merged and the selected hash is calculated.

## Supported links

Supported:

- Direct `http://` file URLs.
- Direct `https://` file URLs.
- Servers that return valid `206 Partial Content` responses for HTTP Range requests.

Not supported:

- Regular web pages instead of direct file URLs.
- Browser-only download flows.
- CAPTCHA, JavaScript token flows, browser-only cookies, or interactive login pages.
- Servers that reject HTTP Range requests.
- Bypassing authentication, paywalls, rate limits, access controls, or copyright restrictions.

## ForceBindIP installation

ForceBindIP is required when the application binds aria2 to a selected local IPv4 interface.

ForceBindIP is a third-party freeware/proprietary tool. Its official project page does not provide a clearly identified open-source license or redistribution permission. Therefore, this repository does **not** bundle ForceBindIP binaries.

### Install ForceBindIP

1. Download ForceBindIP only from its official project page:

   [https://r1ch.net/projects/forcebindip](https://r1ch.net/projects/forcebindip)

2. Download the ZIP/manual-install version from the official source.
3. Extract the official files into:

   ```text
   MultiNIC-Downloader\ForceBindIP\
   ```

4. Keep the official executable and DLL files together. Depending on the release, files may include:

   ```text
   ForceBindIP\
   ├─ ForceBindIP.exe
   ├─ ForceBindIP64.exe
   └─ BindIP.dll
   ```

Do not separate the ForceBindIP executable from `BindIP.dll`. ForceBindIP uses DLL injection, so Windows Security or antivirus products may warn about its behavior. Download only from the official website and read its original documentation.

## aria2

This application uses `aria2c.exe` as the download engine.

- Official project: [aria2.github.io](https://aria2.github.io/)
- Source code: [github.com/aria2/aria2](https://github.com/aria2/aria2)
- License: GNU General Public License, version 2 or later (`GPL-2.0-or-later`)

If you distribute `aria2c.exe` with a release, retain its copyright and license notices, provide the GPL license text, and provide corresponding-source information. See `THIRD_PARTY_NOTICES.md`.

## Python dependencies

The source edition installs the following packages from `requirements.txt`:

```text
requests
psutil
customtkinter
```

- `requests`: HTTP validation and download-related requests.
- `psutil`: detection of active IPv4 network interfaces.
- `customtkinter`: optional compatibility UI dependency.

Do not delete `.venv` unless you want `Running.bat` to recreate the local environment and reinstall Python packages.

## Configuration

The application creates `config.json` locally after settings are saved. This is local user data; do **not** commit it to GitHub.

Example configuration:

```json
{
  "language": "en",
  "output_dir": "C:/Users/YourName/Downloads",
  "max_parallel_tasks": 1,
  "segments_per_interface": 2,
  "segment_max_retries": 5,
  "retry_delay_seconds": 3,
  "hash_algorithm": "SHA256",
  "selected_interfaces": []
}
```

Use `config.example.json` as a safe template.

## Important limitations

- Some hosts may throttle, reject, or temporarily block concurrent connections.
- A server can support Range requests while still applying bandwidth or connection limits.
- Multiple adapters may share the same physical Internet connection, so using all of them may not increase speed.
- VPN, Docker, Hyper-V, VMware, VirtualBox, Tailscale, WireGuard, TAP, and similar virtual adapters may not appear in the interface list.
- Removing a task from the queue removes it from the UI only; temporary files are not automatically deleted.
- This application is not designed to bypass service restrictions or access unauthorized content.

## Project structure

```text
MultiNIC-Downloader/
├─ Running.bat                 # Windows launcher
├─ main.py                     # Application entry point
├─ tkinter_app.py              # Main UI and download coordination
├─ customtkinter_app.py        # Compatibility UI wrapper
├─ dependency_manager.py       # Dependency diagnostics/installer
├─ hash_utils.py               # Hash utilities
├─ network_utils.py            # URL and network helpers
├─ translations.py             # English and Vietnamese UI strings
├─ requirements.txt            # Python dependency list
├─ config.example.json         # Safe example settings
├─ README.md                   # This document
├─ LICENSE                     # License for this project's source code
├─ THIRD_PARTY_NOTICES.md      # Third-party notices
├─ aria2c.exe                  # aria2 runtime executable, if included
└─ ForceBindIP/                # User-installed ForceBindIP files; not bundled
```

## Run source manually

From PowerShell in the project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python .\main.py
```

## Verify source syntax

```powershell
python -m py_compile main.py tkinter_app.py customtkinter_app.py dependency_manager.py hash_utils.py network_utils.py translations.py
```

No output means Python did not find a syntax error in those files.

## Security and privacy

- The app does not require an account.
- The app does not intentionally collect or upload personal data.
- Download links and local settings are processed on the local machine.
- Only use direct links from sources you trust.
- Review the source code before using it in a security-sensitive environment.
- Antivirus/SmartScreen may warn about unsigned executables and ForceBindIP's DLL-injection behavior. Verify sources and file hashes before running software.

## Reporting issues

Please use GitHub Issues. Include:

- Windows version.
- Python version from `py -3 --version`.
- Whether Python is 3.13.1 or newer.
- Application language: English or Vietnamese.
- Whether the app was launched through `Running.bat`.
- Whether `aria2c.exe` and ForceBindIP are installed correctly.
- A complete error message or traceback.
- Steps to reproduce the issue.
- Do not publish private URLs, private IP addresses, access tokens, or personal data.

## License

The Python source code written for this project is licensed under the terms in `LICENSE`.

`aria2c.exe`, ForceBindIP, Python packages, and other third-party components remain subject to their respective licenses and terms. See `THIRD_PARTY_NOTICES.md`.

---

# Tiếng Việt

## Giới thiệu

Multi-NIC Segment Downloader là ứng dụng desktop Windows để tải file từ link HTTP/HTTPS trực tiếp. App kiểm tra HTTP Range, chia file thành byte-range segment và điều phối tải qua các card mạng IPv4 đang hoạt động mà người dùng chọn.

Ứng dụng sử dụng:

- **aria2c.exe** làm download engine.
- **ForceBindIP** để bind process aria2 vào IP/card mạng IPv4 cục bộ đã chọn.
- **Python + Tkinter** cho giao diện, queue, cấu hình, diagnostics và chuyển đổi English/Vietnamese.

Chỉ sử dụng phần mềm cho file và dịch vụ mà bạn có quyền truy cập/tải xuống. Hãy tôn trọng điều khoản dịch vụ, giới hạn tốc độ, bản quyền, access control và pháp luật hiện hành.

## Tính năng

- English là ngôn ngữ mặc định.
- Có Tiếng Việt và chuyển được ngay khi app đang chạy.
- Lưu ngôn ngữ và setting trong `config.json` local.
- Kiểm tra link HTTP/HTTPS trực tiếp.
- Kiểm tra HTTP Range / `206 Partial Content`.
- Logic tải nhiều segment.
- Chọn card mạng IPv4 đang hoạt động.
- Bind theo IP/card qua ForceBindIP.
- Queue và cấu hình task song song.
- Retry độc lập segment lỗi.
- Pause, resume, stop và xóa task khỏi queue.
- Resume qua file tải tạm.
- Chỉ gộp file khi mọi segment hoàn tất hợp lệ.
- Tính SHA256, SHA1 hoặc MD5 sau khi tải hoàn tất.
- Có diagnostics và dependency manager.

## Yêu cầu

- Windows 10 hoặc Windows 11.
- **Python 3.13.1 trở lên, bản 64-bit.**
- **Không hỗ trợ Python 3.13.0** vì có lỗi Tkinter/Tcl đã biết khi chạy virtual environment trên Windows.
- Python phải được cài kèm thành phần **Tcl/Tk and IDLE**.
- Có Internet trong lần chạy đầu để cài Python package.
- Có ít nhất một card mạng IPv4 đang hoạt động.
- Link HTTP/HTTPS trực tiếp.
- Server nguồn hỗ trợ HTTP byte-range request.
- Có `aria2c.exe` ở vị trí ứng dụng yêu cầu.
- Có ForceBindIP trong thư mục `ForceBindIP` đúng cấu trúc.

> Nhiều card mạng không đảm bảo tốc độ tải nhanh hơn. Hiệu quả phụ thuộc routing, giới hạn ISP, băng thông server nguồn, chính sách connection của host và chất lượng từng đường mạng.

## Cài Python đúng cách

App dùng Tkinter, vì vậy cần Tcl/Tk từ Python Windows installer chuẩn.

1. Tải **Python 3.13.x Windows installer 64-bit mới nhất** từ [python.org](https://www.python.org/downloads/windows/).
2. Không dùng Python 3.13.0. Dùng Python **3.13.1 trở lên**.
3. Ở màn hình đầu của installer, chọn:

   ```text
   Add python.exe to PATH
   ```

4. Chọn **Customize installation**.
5. Trong Optional Features, phải chọn:

   ```text
   pip
   Tcl/Tk and IDLE
   Python Launcher / py launcher
   ```

6. Hoàn tất cài đặt và mở PowerShell mới.
7. Kiểm tra Tkinter trước khi chạy app:

   ```powershell
   py -3 -c "import tkinter as tk; root=tk.Tk(); root.withdraw(); root.destroy(); print('Tkinter OK')"
   ```

Kết quả mong đợi:

```text
Tkinter OK
```

Nếu lệnh lỗi, hãy Repair/cài lại Python và bảo đảm chọn **Tcl/Tk and IDLE**.

## Chạy nhanh

1. Tải repository dạng ZIP hoặc clone bằng Git.
2. Giải nén vào thư mục có quyền ghi, ví dụ:

   ```text
   D:\Tools\MultiNIC-Downloader
   ```

3. Cài Python theo hướng dẫn ở trên.
4. Cài ForceBindIP theo phần [Cài ForceBindIP](#cài-forcebindip).
5. Double-click `Running.bat`.
6. Lần chạy đầu, `Running.bat` tạo `.venv` local và cài package trong `requirements.txt`.
7. Nhập link trực tiếp, chọn thư mục lưu, chọn một hoặc nhiều card mạng, rồi nhấn **Add to queue**.

Nếu bạn vừa update/repair Python sau khi `.venv` đã được tạo, hãy xóa `.venv` rồi chạy lại `Running.bat`:

```powershell
Remove-Item -Recurse -Force .\.venv
```

## Cách hoạt động

1. App kiểm tra URL HTTP/HTTPS trực tiếp.
2. App kiểm tra server có hỗ trợ HTTP Range.
3. Download engine chia file thành byte-range segment theo card mạng và setting segment đã chọn.
4. ForceBindIP chạy/bind aria2 vào IP local của card mạng đã chọn.
5. Segment lỗi có thể retry độc lập.
6. File tạm đã hoàn tất được giữ để resume sau pause/stop.
7. Khi mọi segment hợp lệ, app gộp file output và tính HASH đã chọn.

## Link được hỗ trợ

Hỗ trợ:

- Link file trực tiếp dạng `http://`.
- Link file trực tiếp dạng `https://`.
- Server trả `206 Partial Content` hợp lệ cho HTTP Range request.

Không hỗ trợ:

- Trang web thông thường thay vì link file trực tiếp.
- Luồng tải chỉ dùng được bằng browser.
- CAPTCHA, JavaScript token, cookie chỉ có trên browser hoặc trang login tương tác.
- Server từ chối HTTP Range.
- Vượt authentication, paywall, rate limit, access control hoặc giới hạn bản quyền.

## Cài ForceBindIP

ForceBindIP cần thiết khi app bind aria2 vào IP/card mạng IPv4 cục bộ đã chọn.

ForceBindIP là công cụ freeware/proprietary bên thứ ba. Trang chính thức không nêu rõ open-source license hoặc quyền redistribution, vì vậy repository này **không kèm ForceBindIP binary**.

### Các bước cài ForceBindIP

1. Chỉ tải ForceBindIP từ trang chính thức:

   [https://r1ch.net/projects/forcebindip](https://r1ch.net/projects/forcebindip)

2. Tải bản ZIP/manual-install từ nguồn chính thức.
3. Giải nén file chính thức vào:

   ```text
   MultiNIC-Downloader\ForceBindIP\
   ```

4. Giữ executable và DLL của ForceBindIP trong cùng một thư mục. Tùy bản tải về, file có thể gồm:

   ```text
   ForceBindIP\
   ├─ ForceBindIP.exe
   ├─ ForceBindIP64.exe
   └─ BindIP.dll
   ```

Không tách executable khỏi `BindIP.dll`. ForceBindIP dùng DLL injection nên Windows Security/antivirus có thể cảnh báo. Chỉ tải từ website chính thức và đọc tài liệu gốc trước khi dùng.

## aria2

App sử dụng `aria2c.exe` làm download engine.

- Project chính thức: [aria2.github.io](https://aria2.github.io/)
- Source code: [github.com/aria2/aria2](https://github.com/aria2/aria2)
- License: GNU General Public License, version 2 or later (`GPL-2.0-or-later`)

Nếu bạn phát hành `aria2c.exe` kèm release, phải giữ copyright/license notice, cung cấp GPL license text và thông tin source tương ứng. Xem `THIRD_PARTY_NOTICES.md`.

## Python dependencies

Bản source cài các package trong `requirements.txt`:

```text
requests
psutil
customtkinter
```

- `requests`: kiểm tra HTTP và request liên quan tải file.
- `psutil`: phát hiện card mạng IPv4 đang hoạt động.
- `customtkinter`: dependency UI compatibility tùy chọn.

Không xóa `.venv` trừ khi bạn muốn `Running.bat` tạo lại local environment và cài lại package.

## Cấu hình

App tự tạo `config.json` local sau khi lưu setting. Đây là dữ liệu người dùng local; **không** commit lên GitHub.

Ví dụ:

```json
{
  "language": "en",
  "output_dir": "C:/Users/YourName/Downloads",
  "max_parallel_tasks": 1,
  "segments_per_interface": 2,
  "segment_max_retries": 5,
  "retry_delay_seconds": 3,
  "hash_algorithm": "SHA256",
  "selected_interfaces": []
}
```

Dùng `config.example.json` làm mẫu an toàn.

## Giới hạn quan trọng

- Một số host có thể giới hạn tốc độ, từ chối hoặc chặn tạm thời các connection song song.
- Server có thể hỗ trợ Range nhưng vẫn có giới hạn băng thông/kết nối riêng.
- Nhiều adapter có thể dùng cùng một đường Internet vật lý, nên dùng tất cả card chưa chắc tăng tốc.
- VPN, Docker, Hyper-V, VMware, VirtualBox, Tailscale, WireGuard, TAP và adapter ảo tương tự có thể không xuất hiện trong danh sách card mạng.
- Xóa task khỏi queue chỉ xóa khỏi UI; file tạm không tự động bị xóa.
- App không được thiết kế để vượt giới hạn dịch vụ hoặc truy cập nội dung trái phép.

## Cấu trúc project

```text
MultiNIC-Downloader/
├─ Running.bat                 # Windows launcher
├─ main.py                     # Entry point
├─ tkinter_app.py              # UI chính và điều phối download
├─ customtkinter_app.py        # Compatibility UI wrapper
├─ dependency_manager.py       # Dependency diagnostics/installer
├─ hash_utils.py               # Hash utilities
├─ network_utils.py            # URL và network helpers
├─ translations.py             # Chuỗi UI English/Vietnamese
├─ requirements.txt            # Python dependency list
├─ config.example.json         # Mẫu cấu hình an toàn
├─ README.md                   # Tài liệu này
├─ LICENSE                     # License cho source code project
├─ THIRD_PARTY_NOTICES.md      # Third-party notices
├─ aria2c.exe                  # aria2 runtime executable, nếu được kèm
└─ ForceBindIP/                # ForceBindIP do user tự cài; không kèm binary
```

## Chạy source thủ công

Mở PowerShell tại thư mục gốc project:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python .\main.py
```

## Kiểm tra syntax source

```powershell
python -m py_compile main.py tkinter_app.py customtkinter_app.py dependency_manager.py hash_utils.py network_utils.py translations.py
```

Không có output nghĩa là Python không phát hiện lỗi cú pháp trong các file này.

## Bảo mật và quyền riêng tư

- App không yêu cầu tài khoản.
- App không chủ đích thu thập hoặc upload dữ liệu cá nhân.
- Link tải và setting local được xử lý trên máy người dùng.
- Chỉ dùng link trực tiếp từ nguồn tin cậy.
- Hãy review source code trước khi sử dụng trong môi trường nhạy cảm về bảo mật.
- Antivirus/SmartScreen có thể cảnh báo executable chưa ký số và hành vi DLL injection của ForceBindIP. Hãy xác minh nguồn tải/hash file trước khi chạy.

## Báo lỗi

Dùng GitHub Issues. Khi báo lỗi, vui lòng gửi:

- Phiên bản Windows.
- Python version từ `py -3 --version`.
- Xác nhận Python có phải 3.13.1 trở lên không.
- Ngôn ngữ app: English hay Vietnamese.
- Có chạy app qua `Running.bat` hay không.
- `aria2c.exe` và ForceBindIP đã được cài đúng chưa.
- Toàn bộ error message hoặc traceback.
- Các bước tái hiện lỗi.
- Không đăng link riêng tư, private IP, access token hoặc dữ liệu cá nhân.

## License

Source code Python do project này viết được cấp phép theo `LICENSE`.

`aria2c.exe`, ForceBindIP, Python packages và những third-party component khác tuân theo license/điều khoản riêng. Xem `THIRD_PARTY_NOTICES.md`.
