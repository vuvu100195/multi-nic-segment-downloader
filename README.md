# Multi-NIC Segment Downloader

> **A Windows desktop downloader for direct HTTP/HTTPS links, with English and Vietnamese UI.**
>
> **Status:** Public beta. Use at your own risk and report problems through GitHub Issues.

[English](#english) · [Tiếng Việt](#tiếng-việt)

---

# English

## Overview

Multi-NIC Segment Downloader is a Windows desktop application for downloading files from direct HTTP/HTTPS links. It validates HTTP Range support, divides a file into byte-range segments, and can assign download work across selected active IPv4 network interfaces.

The application uses the following runtime components:

- **aria2c.exe** as the download engine.
- **ForceBindIP** to bind the aria2 process to a selected local IPv4 interface/IP.
- **Python + Tkinter** for the user interface, configuration, queue management, diagnostics, and language switching.

Use this software only for files and services that you are authorized to access. Respect website terms, rate limits, copyright, access controls, and applicable law.

## Features

- English is the default UI language.
- Vietnamese UI is available and can be switched while the app is running.
- Persistent language and settings in local `config.json`.
- Direct HTTP/HTTPS link validation.
- HTTP Range / `206 Partial Content` verification before segmented download starts.
- Multi-segment download logic.
- Selection of active IPv4 network interfaces.
- Per-interface IP binding through ForceBindIP.
- Download queue and configurable parallel tasks.
- Independent retry logic for failed segments.
- Pause, resume, stop, and remove-from-queue controls.
- Resume support through temporary download files.
- Final merge only after all segments are valid.
- SHA256, SHA1, and MD5 calculation after download completion.
- Built-in diagnostics and dependency management.

## Requirements

- Windows 10 or Windows 11.
- Python 3.10 or newer.
- Internet access on first run if Python packages must be installed.
- One or more active IPv4 network interfaces.
- A direct HTTP/HTTPS URL.
- A source server that supports HTTP byte-range requests.
- `aria2c.exe` in the application folder.
- ForceBindIP installed in the expected `ForceBindIP` folder.

> Multiple network interfaces do **not** guarantee higher download speed. Actual performance depends on routing, ISP capacity, source-server bandwidth, the host's parallel-connection policy, and the quality of each network path.

## Quick start

1. Download this repository as a ZIP file or clone it with Git.
2. Extract it into a folder where you have write permission, for example:

   ```text
   D:\Tools\MultiNIC-Downloader
   ```

3. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/windows/) if Python is not already installed.
4. During Python setup, enable **Add Python to PATH**.
5. Install ForceBindIP as described in [ForceBindIP installation](#forcebindip-installation).
6. Double-click `Running.bat`.
7. On first run, the launcher may create a local `.venv` environment and install packages listed in `requirements.txt`.
8. Enter a direct download URL, choose an output folder, select one or more network interfaces, and click **Add to queue**.

## How it works

1. The application validates the direct HTTP/HTTPS URL.
2. It checks whether the server supports HTTP Range requests.
3. The download engine divides the file into byte-range segments according to the selected network interfaces and the configured segment count.
4. ForceBindIP starts/binds aria2 for the selected local interface IP.
5. Failed segments can retry independently according to the configured retry policy.
6. Completed temporary segments are retained to support resuming a paused or stopped task.
7. After all segments pass completion checks, the application merges the output and calculates the configured hash.

## Supported links

Supported:

- Direct `http://` file URLs.
- Direct `https://` file URLs.
- Servers that support HTTP Range requests / `206 Partial Content`.

Not supported:

- Normal web pages instead of a direct file URL.
- Download flows that require browser interaction.
- CAPTCHA, JavaScript-based token flows, browser-only cookies, or interactive login pages.
- Servers that reject HTTP Range requests.
- Circumventing authentication, paywalls, rate limits, access controls, or copyright restrictions.

## ForceBindIP installation

ForceBindIP is required at runtime when the application binds aria2 to a chosen local IPv4 interface.

ForceBindIP is a third-party freeware/proprietary tool. Its official project page does not provide a clearly identified open-source license or redistribution permission. Therefore, this repository does **not** bundle ForceBindIP binaries.

### Install ForceBindIP

1. Download ForceBindIP only from its official project page:

   [https://r1ch.net/projects/forcebindip](https://r1ch.net/projects/forcebindip)

2. Download the ZIP/manual-install version from the official source.
3. Extract the official files into this project folder:

   ```text
   MultiNIC-Downloader\ForceBindIP\
   ```

4. Keep the official executable and DLL files together. The exact filenames depend on the downloaded release, but may include:

   ```text
   ForceBindIP\
   ├─ ForceBindIP.exe
   ├─ ForceBindIP64.exe
   └─ BindIP.dll
   ```

Do not separate the ForceBindIP executable from `BindIP.dll`. ForceBindIP uses DLL injection, so Windows security software may show warnings. Download it only from the official website and review the original documentation before use.

## aria2

This application uses `aria2c.exe` as its download engine.

- Official project: [aria2.github.io](https://aria2.github.io/)
- Source code: [github.com/aria2/aria2](https://github.com/aria2/aria2)
- License: GNU General Public License, version 2 or later (`GPL-2.0-or-later`)

If you distribute `aria2c.exe` with a release, you must retain its copyright and license notices, provide the GPL license text, and provide corresponding-source information. See `THIRD_PARTY_NOTICES.md`.

## Python dependencies

The source edition requires the packages listed in `requirements.txt`:

```text
requests
psutil
```

- `requests`: HTTP validation and download-related requests.
- `psutil`: detection of active IPv4 network interfaces.

If `Running.bat` creates a `.venv` folder, do not delete it unless you intentionally want it recreated and the dependencies installed again.

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
- Multiple adapters may use the same physical Internet connection; using all of them may not increase speed.
- VPN, Docker, Hyper-V, VMware, VirtualBox, Tailscale, WireGuard, TAP, and other virtual adapters may not appear in the interface list.
- Removing a task from the queue removes it from the UI only; temporary files are not automatically deleted.
- Pause and stop are intended to preserve temporary data for resuming.
- This project is not a tool for bypassing service restrictions or accessing unauthorized content.

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
├─ LICENSE                     # License for this project's own source code
├─ THIRD_PARTY_NOTICES.md      # Third-party notices
├─ aria2c.exe                  # aria2 runtime executable, if included
└─ ForceBindIP/                # User-installed ForceBindIP files; not bundled
```

## Run source manually

If you do not use `Running.bat`, run these commands from PowerShell in the project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python .\main.py
```

## Verify source syntax

Run this command from the project root:

```powershell
python -m py_compile main.py tkinter_app.py customtkinter_app.py dependency_manager.py hash_utils.py network_utils.py translations.py
```

No output means Python did not find a syntax error in those files.

## Security and privacy

- The app does not require an account.
- The app does not intentionally collect or upload personal data.
- Download links and local configuration are processed on the local machine.
- Only use direct links from sources you trust.
- Review the source code before using it in a security-sensitive environment.
- Antivirus or SmartScreen may warn about unsigned executables and ForceBindIP's DLL injection behavior. Verify sources and file hashes before running software.

## Reporting issues

Please use GitHub Issues. Include:

- Windows version.
- Python version from `python --version` or `py --version`.
- Application language: English or Vietnamese.
- Whether you ran the app through `Running.bat`.
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

Multi-NIC Segment Downloader là ứng dụng desktop Windows dùng để tải file từ link HTTP/HTTPS trực tiếp. App kiểm tra HTTP Range, chia file thành các byte-range segment và có thể phân bổ tải qua các card mạng IPv4 đang hoạt động mà người dùng chọn.

Ứng dụng sử dụng các thành phần runtime sau:

- **aria2c.exe** làm download engine.
- **ForceBindIP** để bind process aria2 vào card mạng/IP IPv4 cục bộ đã chọn.
- **Python + Tkinter** cho giao diện, cấu hình, queue, diagnostics và chuyển đổi ngôn ngữ.

Chỉ sử dụng phần mềm cho file và dịch vụ mà bạn có quyền truy cập/tải xuống. Hãy tôn trọng điều khoản website, giới hạn tốc độ, bản quyền, access control và pháp luật hiện hành.

## Tính năng

- English là ngôn ngữ giao diện mặc định.
- Có Tiếng Việt và có thể chuyển ngôn ngữ khi app đang chạy.
- Lưu ngôn ngữ và cấu hình trong `config.json` local.
- Kiểm tra link HTTP/HTTPS trực tiếp.
- Kiểm tra HTTP Range / `206 Partial Content` trước khi tải nhiều segment.
- Logic tải nhiều segment.
- Chọn các card mạng IPv4 đang hoạt động.
- Bind theo IP của từng card mạng qua ForceBindIP.
- Hàng chờ và cấu hình task song song.
- Retry độc lập các segment lỗi.
- Pause, resume, stop và xóa task khỏi queue.
- Hỗ trợ tiếp tục tải thông qua file tạm.
- Chỉ gộp file khi mọi segment hợp lệ.
- Tính SHA256, SHA1 hoặc MD5 sau khi tải hoàn tất.
- Có diagnostics và dependency manager trong app.

## Yêu cầu

- Windows 10 hoặc Windows 11.
- Python 3.10 trở lên.
- Có Internet trong lần chạy đầu nếu cần cài package Python.
- Có ít nhất một card mạng IPv4 đang hoạt động.
- Link HTTP/HTTPS trực tiếp.
- Server nguồn hỗ trợ HTTP byte-range request.
- Có `aria2c.exe` trong thư mục ứng dụng.
- Có ForceBindIP trong thư mục `ForceBindIP` theo đúng cấu trúc yêu cầu.

> Nhiều card mạng không đảm bảo tốc độ tải cao hơn. Hiệu quả thực tế phụ thuộc vào routing, giới hạn ISP, băng thông server nguồn, chính sách kết nối song song của host và chất lượng từng đường mạng.

## Chạy nhanh

1. Tải repository dạng ZIP hoặc clone bằng Git.
2. Giải nén vào thư mục bạn có quyền ghi, ví dụ:

   ```text
   D:\Tools\MultiNIC-Downloader
   ```

3. Cài Python 3.10 trở lên từ [python.org](https://www.python.org/downloads/windows/) nếu máy chưa cài Python.
4. Khi cài Python, chọn **Add Python to PATH**.
5. Cài ForceBindIP theo phần [Cài ForceBindIP](#cài-forcebindip).
6. Double-click `Running.bat`.
7. Trong lần chạy đầu, launcher có thể tạo môi trường `.venv` cục bộ và cài package trong `requirements.txt`.
8. Nhập link tải trực tiếp, chọn thư mục lưu, chọn một hoặc nhiều card mạng, rồi nhấn **Add to queue**.

## Cách hoạt động

1. App kiểm tra URL HTTP/HTTPS trực tiếp.
2. App kiểm tra server có hỗ trợ HTTP Range hay không.
3. Download engine chia file thành các byte-range segment theo số card mạng đã chọn và số segment đã cấu hình.
4. ForceBindIP chạy/bind aria2 vào IP local của card mạng được chọn.
5. Các segment lỗi có thể retry độc lập theo retry policy đã cấu hình.
6. Segment tạm hoàn tất được giữ lại để hỗ trợ resume task đã pause hoặc stop.
7. Sau khi mọi segment hợp lệ, app gộp output và tính HASH đã chọn.

## Link được hỗ trợ

Hỗ trợ:

- Link file trực tiếp dạng `http://`.
- Link file trực tiếp dạng `https://`.
- Server hỗ trợ HTTP Range / `206 Partial Content`.

Không hỗ trợ:

- Trang web thông thường thay vì URL file trực tiếp.
- Luồng tải cần thao tác trình duyệt.
- CAPTCHA, luồng token JavaScript, cookie chỉ có trên browser hoặc trang đăng nhập tương tác.
- Server từ chối HTTP Range.
- Vượt qua authentication, paywall, rate limit, access control hoặc hạn chế bản quyền.

## Cài ForceBindIP

ForceBindIP cần thiết khi ứng dụng bind aria2 vào IP IPv4/card mạng cục bộ đã chọn.

ForceBindIP là công cụ freeware/proprietary bên thứ ba. Trang chính thức không cung cấp rõ ràng một open-source license hoặc quyền redistribution. Vì vậy, repository này **không đóng gói ForceBindIP binary**.

### Các bước cài ForceBindIP

1. Chỉ tải ForceBindIP từ trang chính thức:

   [https://r1ch.net/projects/forcebindip](https://r1ch.net/projects/forcebindip)

2. Tải bản ZIP/manual-install từ nguồn chính thức.
3. Giải nén các file chính thức vào thư mục:

   ```text
   MultiNIC-Downloader\ForceBindIP\
   ```

4. Giữ file executable và DLL của ForceBindIP trong cùng thư mục. Tùy bản tải về, các file có thể gồm:

   ```text
   ForceBindIP\
   ├─ ForceBindIP.exe
   ├─ ForceBindIP64.exe
   └─ BindIP.dll
   ```

Không tách ForceBindIP executable khỏi `BindIP.dll`. ForceBindIP sử dụng DLL injection nên Windows Security/antivirus có thể cảnh báo. Chỉ tải từ website chính thức và đọc tài liệu gốc trước khi sử dụng.

## aria2

Ứng dụng sử dụng `aria2c.exe` làm download engine.

- Project chính thức: [aria2.github.io](https://aria2.github.io/)
- Source code: [github.com/aria2/aria2](https://github.com/aria2/aria2)
- License: GNU General Public License, version 2 or later (`GPL-2.0-or-later`)

Nếu bạn phát hành `aria2c.exe` kèm theo release, bạn phải giữ copyright/license notice, cung cấp GPL license text và thông tin source tương ứng. Xem `THIRD_PARTY_NOTICES.md`.

## Python dependencies

Bản source cần package trong `requirements.txt`:

```text
requests
psutil
```

- `requests`: kiểm tra HTTP và các request liên quan tải file.
- `psutil`: phát hiện các network interface IPv4 đang hoạt động.

Nếu `Running.bat` tạo thư mục `.venv`, không nên xóa trừ khi bạn muốn app tạo lại môi trường và cài lại dependency.

## Cấu hình

App tạo `config.json` local sau khi bạn lưu setting. Đây là dữ liệu người dùng local; **không** commit file này lên GitHub.

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

- Một số host có thể giới hạn tốc độ, từ chối hoặc chặn tạm thời nhiều connection song song.
- Server có thể hỗ trợ Range nhưng vẫn áp dụng giới hạn băng thông/kết nối riêng.
- Nhiều adapter có thể dùng cùng một đường Internet vật lý; dùng tất cả card không đồng nghĩa tốc độ tăng.
- VPN, Docker, Hyper-V, VMware, VirtualBox, Tailscale, WireGuard, TAP và adapter ảo khác có thể không hiện trong danh sách card mạng.
- Xóa task khỏi queue chỉ xóa khỏi UI; file tạm không bị tự động xóa.
- Pause và stop được thiết kế để giữ dữ liệu tạm cho resume.
- Dự án không dùng để vượt qua giới hạn dịch vụ hoặc truy cập nội dung không được cho phép.

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
├─ requirements.txt            # Danh sách Python dependency
├─ config.example.json         # Mẫu cấu hình an toàn
├─ README.md                   # Tài liệu này
├─ LICENSE                     # License cho source code do project viết
├─ THIRD_PARTY_NOTICES.md      # Third-party notices
├─ aria2c.exe                  # aria2 runtime executable, nếu được kèm
└─ ForceBindIP/                # ForceBindIP người dùng tự cài; không kèm binary
```

## Chạy source thủ công

Nếu không dùng `Running.bat`, mở PowerShell trong thư mục project và chạy:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python .\main.py
```

## Kiểm tra syntax source

Chạy lệnh sau tại thư mục gốc project:

```powershell
python -m py_compile main.py tkinter_app.py customtkinter_app.py dependency_manager.py hash_utils.py network_utils.py translations.py
```

Không có output nghĩa là Python không phát hiện lỗi cú pháp trong các file này.

## Bảo mật và quyền riêng tư

- App không yêu cầu tài khoản.
- App không chủ đích thu thập hoặc upload dữ liệu cá nhân.
- Link tải và cấu hình local được xử lý trên máy người dùng.
- Chỉ dùng link trực tiếp từ nguồn bạn tin cậy.
- Hãy review source code trước khi dùng trong môi trường nhạy cảm về bảo mật.
- Antivirus/SmartScreen có thể cảnh báo executable chưa ký số và hành vi DLL injection của ForceBindIP. Hãy xác minh nguồn tải và hash file trước khi chạy.

## Báo lỗi

Hãy dùng GitHub Issues. Khi báo lỗi, vui lòng gửi:

- Phiên bản Windows.
- Phiên bản Python từ `python --version` hoặc `py --version`.
- Ngôn ngữ app: English hay Vietnamese.
- Có chạy app qua `Running.bat` hay không.
- `aria2c.exe` và ForceBindIP đã được cài đúng chưa.
- Toàn bộ error message hoặc traceback.
- Các bước tái hiện lỗi.
- Không đăng link riêng tư, IP riêng tư, token truy cập hoặc dữ liệu cá nhân.

## License

Source code Python do project này viết được cấp phép theo file `LICENSE`.

`aria2c.exe`, ForceBindIP, các package Python và những third-party component khác tuân theo license/điều khoản riêng của chúng. Xem `THIRD_PARTY_NOTICES.md`.
