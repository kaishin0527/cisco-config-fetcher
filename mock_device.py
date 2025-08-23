

import asyncio
import logging

import socketserver
from threading import Thread

# Telnet mock server
class MockTelnetServer(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        self.buffer = b''
        print("Telnet接続が確立されました")

    
    def data_received(self, data):
        self.buffer += data
        print(f"受信データ: {data}")
        
        # 改行でコマンドを分割
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            command = line.decode().strip()
            print(f"受信コマンド: {command}")
            
            if command == "show version":
                response = "Cisco IOS Software, Version 15.2(4)M5\nCompiled Thu 21-Aug-14 15:30 by builder"
            elif command == "show running-config":
                response = "Building configuration...\nCurrent configuration : 1000 bytes\n!"
            else:
                response = f"Unknown command: {command}"
            
            self.transport.write(response.encode() + b"\r\nmock-device# ")

class TelnetMock:
    def __init__(self, port=2323):
        self.port = port
        self.server = None
    
    async def start(self):
        loop = asyncio.get_event_loop()
        self.server = await loop.create_server(
            MockTelnetServer,
            '127.0.0.1',
            self.port
        )
        print(f"Telnetモックサーバーがポート{self.port}で起動しました")
        await self.server.serve_forever()

# SSH mock server
class MockSSHServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

class MockSSHHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print("SSH接続が確立されました")
        
        # SSHプロトコルバナーの送信
        self.request.sendall(b"SSH-2.0-MockSSHServer\r\n")
        
        # SSH認証の簡易実装
        try:
            # クライアントからの認証情報待ち
            auth_data = self.request.recv(1024)
            if auth_data:
                # 簡易的に認証成功とみなす
                self.request.sendall(b"Authentication successful\r\n")
                
                # プロンプト送信
                self.request.sendall(b"mock-device# ")
                
                while True:
                    try:
                        data = self.request.recv(1024)
                        if not data:
                            break
                        
                        command = data.decode().strip()
                        print(f"受信コマンド: {command}")
                        
                        if command == "show version":
                            response = "Cisco IOS Software, Version 15.2(4)M5\nCompiled Thu 21-Aug-14 15:30 by builder"
                        elif command == "show running-config":
                            response = "Building configuration...\nCurrent configuration : 1000 bytes\n!"
                        else:
                            response = f"Unknown command: {command}"
                        
                        self.request.sendall(response.encode() + b"\r\nmock-device# ")
                    except Exception as e:
                        print(f"SSHハンドラーエラー: {e}")
                        break
        except Exception as e:
            print(f"SSHハンドラー初期化エラー: {e}")

def start_ssh_mock(port=2222):
    server = MockSSHServer(('127.0.0.1', port), MockSSHHandler)
    print(f"SSHモックサーバーがポート{port}で起動しました")
    server.serve_forever()

# モックサーバーの起動
def start_mock_servers():
    # Telnetサーバーの非同期起動
    telnet_thread = Thread(target=lambda: asyncio.run(TelnetMock().start()))
    telnet_thread.daemon = True
    telnet_thread.start()
    
    # SSHサーバーの起動
    ssh_thread = Thread(target=start_ssh_mock)
    ssh_thread.daemon = True
    ssh_thread.start()
    
    return telnet_thread, ssh_thread

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "start":
        start_mock_servers()
        print("モックサーバーが起動中です (Telnet: 2323, SSH: 2222)")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            print("モックサーバーを終了します")
    else:
        print("使用方法: python mock_device.py start")
