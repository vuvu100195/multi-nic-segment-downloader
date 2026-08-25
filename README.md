# Multi-NIC Segment Downloader

> **Windows desktop downloader for direct HTTP/HTTPS links, with English and Vietnamese UI.**
>
> This project is currently a public beta. Please report issues through GitHub Issues and include the error message, Windows version, Python version, and steps to reproduce the problem.

[English](#english) · [Tiếng Việt](#tiếng-việt)

---

# English

## Overview

Multi-NIC Segment Downloader is a Windows desktop application for downloading files from direct HTTP/HTTPS links. It validates HTTP Range support, divides a file into byte-range segments, and can assign segments across selected active IPv4 network interfaces.

The application is intended for legitimate downloads only. Use it only for files and services that you are authorized to access, and respect each provider's terms of service, rate limits, and applicable law.

## Features

- English is the default interface language; Vietnamese is available and can be switched while the app is running.
- Remembers the selected language and app settings in `config.json`.
- Accepts direct HTTP/HTTPS download links.
- Verifies that the server supports HTTP byte ranges (`206 Partial Content`) before a multi-segment download starts.
- Splits a file into byte-range segments.
- Lets you select active IPv4 network interfaces for a download.
- Binds each segment connection to the selected interface IP.
- Retries failed segments independently.
- Keeps completed temporary segment files for resume support.
- Supports a task queue and configurable parallel downloads.
- Supports pause, resume, and stop controls.
- Merges segments only after every segment has completed successfully.
- Calculates SHA256, SHA1, or MD5 after the merged file is created.
- Includes a diagnostics screen and an in-app dependency manager.

## Requirements

- Windows 10 or Windows 11.
- Python 3.10 or newer.
- Internet access on the first run, so required Python packages can be installed.
- One or more active IPv4 network interfaces.
- A direct HTTP/HTTPS URL.
- A download server that correctly supports HTTP Range requests.

> Multiple network interfaces do not guarantee higher download speed. Actual performance depends on routing, ISP limits, source-server limits, and the server's policy for parallel HTTP connections.

## Quick start

1. Download this repository as ZIP or clone it with Git.
2. Extract it to a folder where you have write permission, for example `D:\Tools\MultiNIC-Downloader`.
3. Install Python 3.10 or later from [python.org](https://www.python.org/downloads/windows/) if it is not already installed.
4. During Python installation, enable **Add Python to PATH**.
5. Double-click `Running.bat`.
6. On the first run, the launcher can create a local `.venv` environment and install dependencies from `requirements.txt`.
7. Enter a direct link, choose an output folder, select one or more network cards, and click **Add to queue**.

## How it works

1. The app validates the URL and probes the server with a `Range: bytes=0-0` request.
2. The app continues only when the server responds with a valid `206 Partial Content` response and `Content-Range` header.
3. The file is split into segments according to the selected network interfaces and the **Segments per Part/card** setting.
4. Each segment is requested with an HTTP `Range` header and a socket bound to the assigned local interface IP.
5. Completed segments are preserved as hidden `.part` files in the output folder.
6. After all segments are valid, they are merged in the original byte order.
7. The final file size is checked, then the selected hash algorithm is calculated.

## First-run dependencies

The application needs the following Python packages:

```text
requests
psutil
```

They are listed in `requirements.txt`.

- `requests` is used for HTTP probing and segmented HTTP downloads.
- `psutil` is used to detect active IPv4 network interfaces.

If `Running.bat` creates a local `.venv` folder, do not delete it unless you intentionally want the launcher to recreate the environment and reinstall packages.

## Supported links

Supported:

- Direct `http://` links.
- Direct `https://` links.
- Servers that return valid HTTP `206 Partial Content` responses for byte-range requests.

Not supported:

- Web pages instead of direct file URLs.
- Download pages requiring manual browser interaction.
- Servers that do not support HTTP Range requests.
- Proxy environment mode in multi-NIC mode.
- Authentication flows that require cookies, JavaScript, CAPTCHA, or a browser login.

## Important limitations

- Some hosts may rate-limit, reject, or temporarily block many parallel requests.
- A host can support Range requests but still impose its own connection or bandwidth limits.
- VPN, virtual adapters, Docker, Hyper-V, VMware, VirtualBox, Tailscale, WireGuard, TAP, and similar adapters may be excluded from the interface list.
- Pausing or stopping a task keeps temporary segment files so that a future resume can continue from existing data.
- Removing a task from the queue removes it from the UI only; temporary files are not automatically deleted.
- The app does not bypass paywalls, access controls, service limits, authentication, or copyright restrictions.

## Configuration

The app automatically creates `config.json` after settings are saved. This file is local user data and should not be committed to GitHub.

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

A safe template is available as `config.example.json`.

## Project structure

```text
MultiNIC-Segment-Downloader/
├─ Running.bat                 # Windows launcher
├─ main.py                     # Application entry point
├─ tkinter_app.py              # Main Tkinter UI and download manager
├─ customtkinter_app.py        # Compatibility UI wrapper
├─ dependency_manager.py       # Dependency diagnostics and installer
├─ hash_utils.py               # Hash calculation helpers
├─ network_utils.py            # URL, HTTP Range, and network helpers
├─ translations.py             # English and Vietnamese translations
├─ requirements.txt            # Python dependency list
├─ config.example.json         # Safe sample configuration
├─ README.md                   # This document
├─ LICENSE                     # Project license
└─ THIRD_PARTY_NOTICES.md      # Third-party notices, if applicable
```

## Development run

To run the source manually instead of using `Running.bat`:

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
- Download URLs and local settings are processed on your machine.
- Use direct links only when you trust the source.
- Review this source code yourself before using it in security-sensitive environments.

## Third-party software

This repository may contain or be distributed together with third-party utilities such as `aria2c.exe` and ForceBindIP.

Only include a third-party binary in a release if the application actually uses it. Keep each third-party tool's original license, copyright notices, and redistribution terms. See `THIRD_PARTY_NOTICES.md` for the exact notices included with a release.

This project is not affiliated with aria2, ForceBindIP, Python, Requests, psutil, or GitHub.

## Contributing

Contributions, bug reports, translation improvements, and test results are welcome.

When reporting a bug, include:

- Windows version.
- Python version from `python --version` or `py --version`.
- App language: English or Vietnamese.
- Whether the app was launched through `Running.bat`.
- The direct-link type, without publishing private or sensitive URLs.
- The complete error message or traceback.
- Steps that reproduce the issue.

## License

See the `LICENSE` file for this project's license.

---

# Tiếng Việt

## Giới thiệu

Multi-NIC Segment Downloader là ứng dụng desktop cho Windows dùng để tải file từ link HTTP/HTTPS trực tiếp. Ứng dụng kiểm tra HTTP Range, chia file thành các byte-range segment và có thể phân bổ segment qua các card mạng IPv4 đang hoạt động mà người dùng chọn.

Dự án hiện ở giai đoạn public beta. Nếu gặp lỗi, hãy tạo GitHub Issue và gửi kèm thông báo lỗi, phiên bản Windows, phiên bản Python và các bước để tái hiện lỗi.

Chỉ sử dụng ứng dụng cho các file và dịch vụ mà bạn có quyền truy cập/tải xuống. Hãy tôn trọng điều khoản dịch vụ, giới hạn băng thông, giới hạn kết nối và pháp luật hiện hành.

## Tính năng

- English là ngôn ngữ mặc định; hỗ trợ Tiếng Việt và đổi ngôn ngữ ngay khi app đang chạy.
- Lưu ngôn ngữ và cấu hình ứng dụng trong `config.json`.
- Nhận link tải HTTP/HTTPS trực tiếp.
- Kiểm tra server có hỗ trợ HTTP byte range (`206 Partial Content`) trước khi tải nhiều segment.
- Chia file thành các segment byte range.
- Cho phép chọn card mạng IPv4 đang hoạt động cho từng file tải.
- Bind kết nối của segment vào IP của card mạng đã chọn.
- Retry độc lập từng segment lỗi.
- Giữ file segment tạm để hỗ trợ tiếp tục tải.
- Có hàng chờ và cấu hình số task song song.
- Có pause, resume và stop.
- Chỉ gộp file sau khi mọi segment tải hoàn tất hợp lệ.
- Tính SHA256, SHA1 hoặc MD5 sau khi gộp file.
- Có mục diagnostics và dependency manager trong ứng dụng.

## Yêu cầu

- Windows 10 hoặc Windows 11.
- Python 3.10 trở lên.
- Có Internet trong lần chạy đầu để cài các package Python cần thiết.
- Có ít nhất một card mạng IPv4 đang hoạt động.
- Link tải HTTP/HTTPS trực tiếp.
- Server tải file phải hỗ trợ HTTP Range đúng cách.

> Nhiều card mạng không đảm bảo tốc độ tải nhanh hơn. Hiệu quả thực tế phụ thuộc vào routing, giới hạn ISP, giới hạn của server nguồn và chính sách kết nối song song của server.

## Chạy nhanh

1. Tải repository dưới dạng ZIP hoặc clone bằng Git.
2. Giải nén vào thư mục có quyền ghi, ví dụ `D:\Tools\MultiNIC-Downloader`.
3. Cài Python 3.10 trở lên từ [python.org](https://www.python.org/downloads/windows/) nếu máy chưa có Python.
4. Trong lúc cài Python, chọn **Add Python to PATH**.
5. Double-click file `Running.bat`.
6. Ở lần chạy đầu, launcher có thể tạo môi trường `.venv` cục bộ và cài thư viện từ `requirements.txt`.
7. Nhập link trực tiếp, chọn thư mục lưu, chọn một hoặc nhiều card mạng, rồi nhấn **Add to queue**.

## Cách hoạt động

1. App kiểm tra URL và gửi request `Range: bytes=0-0` đến server.
2. App chỉ tiếp tục nếu server trả về `206 Partial Content` hợp lệ cùng header `Content-Range`.
3. File được chia segment theo số card mạng đã chọn và thông số **Segments per Part/card**.
4. Mỗi segment dùng HTTP `Range` và socket được bind vào IP local của card mạng đã phân bổ.
5. Segment đã hoàn tất được giữ lại dưới dạng file `.part` ẩn trong thư mục output.
6. Khi mọi segment hợp lệ, app gộp chúng theo đúng thứ tự byte ban đầu.
7. App kiểm tra kích thước file cuối và tính HASH theo thuật toán đã chọn.

## Thư viện lần đầu chạy

Ứng dụng cần các package Python sau:

```text
requests
psutil
```

Các package này được liệt kê trong `requirements.txt`.

- `requests` dùng cho HTTP probe và tải HTTP segment.
- `psutil` dùng để phát hiện card mạng IPv4 đang hoạt động.

Nếu `Running.bat` tạo thư mục `.venv`, không nên xóa thư mục này trừ khi bạn muốn launcher tạo lại môi trường và cài lại thư viện.

## Link được hỗ trợ

Hỗ trợ:

- Link trực tiếp dạng `http://`.
- Link trực tiếp dạng `https://`.
- Server trả về đúng HTTP `206 Partial Content` cho byte-range request.

Không hỗ trợ:

- Trang web thay vì link file trực tiếp.
- Trang tải cần thao tác bằng trình duyệt.
- Server không hỗ trợ HTTP Range.
- Proxy environment mode khi chạy multi-NIC.
- Quy trình xác thực cần cookie, JavaScript, CAPTCHA hoặc đăng nhập trên trình duyệt.

## Giới hạn quan trọng

- Một số host có thể giới hạn tốc độ, từ chối hoặc chặn tạm thời nhiều request song song.
- Server có thể hỗ trợ Range nhưng vẫn áp dụng giới hạn kết nối hoặc băng thông riêng.
- VPN, adapter ảo, Docker, Hyper-V, VMware, VirtualBox, Tailscale, WireGuard, TAP và các adapter tương tự có thể không xuất hiện trong danh sách card mạng.
- Pause hoặc stop task sẽ giữ file segment tạm để có thể resume sau này.
- Xóa task khỏi queue chỉ xóa khỏi giao diện; file tạm không bị tự động xóa.
- App không dùng để vượt paywall, kiểm soát truy cập, giới hạn dịch vụ, xác thực hoặc hạn chế bản quyền.

## Cấu hình

App tự tạo `config.json` sau khi lưu cài đặt. Đây là dữ liệu local của người dùng, không nên commit lên GitHub.

Mẫu cấu hình:

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

## Chạy source thủ công

Nếu không dùng `Running.bat`, chạy từ PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python .\main.py
```

## Kiểm tra syntax source

Chạy lệnh sau trong thư mục project:

```powershell
python -m py_compile main.py tkinter_app.py customtkinter_app.py dependency_manager.py hash_utils.py network_utils.py translations.py
```

Không có output nghĩa là Python không phát hiện lỗi cú pháp trong các file đó.

## Bảo mật và quyền riêng tư

- App không yêu cầu tài khoản.
- App không chủ đích thu thập hoặc upload dữ liệu cá nhân.
- Link tải và cấu hình local được xử lý trên máy của bạn.
- Chỉ dùng link trực tiếp từ nguồn bạn tin cậy.
- Hãy tự review source code trước khi dùng trong môi trường nhạy cảm về bảo mật.

## Phần mềm bên thứ ba

Repository hoặc bản phát hành có thể đi kèm công cụ bên thứ ba như `aria2c.exe` và ForceBindIP.

Chỉ đưa binary bên thứ ba vào bản phát hành khi app thực sự sử dụng chúng. Phải giữ lại license, copyright notice và điều khoản phân phối gốc của từng công cụ. Xem `THIRD_PARTY_NOTICES.md` để biết thông báo license chính xác trong từng bản release.

Dự án này không liên kết chính thức với aria2, ForceBindIP, Python, Requests, psutil hoặc GitHub.

## Đóng góp và báo lỗi

Hoan nghênh đóng góp code, báo lỗi, cải thiện bản dịch và kết quả test.

Khi báo lỗi, vui lòng gửi:

- Phiên bản Windows.
- Phiên bản Python từ `python --version` hoặc `py --version`.
- Ngôn ngữ app đang dùng: English hay Vietnamese.
- App có được chạy bằng `Running.bat` hay không.
- Loại link tải, nhưng không đăng link riêng tư hoặc nhạy cảm.
- Toàn bộ error message hoặc traceback.
- Các bước có thể tái hiện lỗi.

## License

Xem file `LICENSE` để biết license của dự án.
