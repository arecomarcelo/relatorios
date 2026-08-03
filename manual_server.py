import http.server
import os
import socketserver
import threading
import webbrowser
from urllib.parse import unquote


class ManualHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)

    def do_GET(self):
        if self.path == "/manual" or self.path == "/manual/":
            self.send_manual()
        else:
            super().do_GET()

    def send_manual(self):
        try:
            # Ler o conteúdo do manual
            manual_path = "documentacao/Manual_Relatorio_Vendas.md"

            with open(manual_path, "r", encoding="utf-8") as file:
                markdown_content = file.read()

            # Converter para HTML com tema dark
            html_content = self.convert_markdown_to_dark_html(markdown_content)

            # Enviar resposta
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))

        except Exception as e:
            self.send_error(500, f"Erro ao carregar manual: {str(e)}")

    def convert_markdown_to_dark_html(self, markdown_content):
        """
        Converte markdown para HTML com tema dark
        """
        try:
            import markdown

            html = markdown.markdown(
                markdown_content,
                extensions=["tables", "fenced_code", "toc", "codehilite"],
            )
        except ImportError:
            html = self.basic_markdown_to_html(markdown_content)

        return f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>📖 Manual do Relatório de Vendas - Relatórios</title>
            <style>
                :root {{
                    --primary-color: #1E88E5;
                    --secondary-color: #1976D2;
                    --accent-color: #1565C0;
                    --bg-primary: #121212;
                    --bg-secondary: #1e1e1e;
                    --bg-tertiary: #2d2d2d;
                    --text-primary: #ffffff;
                    --text-secondary: #b0b0b0;
                    --border-color: #404040;
                }}
                
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Roboto', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: var(--bg-primary);
                    color: var(--text-primary);
                    line-height: 1.8;
                    overflow-x: hidden;
                }}
                
                .header {{
                    display: none;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 30px;
                    background: var(--bg-secondary);
                    box-shadow: 0 0 30px rgba(0,0,0,0.5);
                    border-radius: 15px;
                    margin-top: 0;
                    margin-bottom: 30px;
                    min-height: 100vh;
                }}
                
                h1, h2, h3, h4, h5, h6 {{
                    color: var(--primary-color);
                    margin-top: 30px;
                    margin-bottom: 15px;
                    font-weight: 600;
                }}
                
                h1 {{
                    border-bottom: 3px solid var(--primary-color);
                    padding-bottom: 10px;
                    font-size: 2.2rem;
                }}
                
                h2 {{
                    border-left: 4px solid var(--secondary-color);
                    padding-left: 15px;
                    font-size: 1.8rem;
                    color: var(--secondary-color);
                }}
                
                h3 {{
                    color: var(--accent-color);
                    font-size: 1.4rem;
                }}
                
                h4 {{
                    color: var(--primary-color);
                    font-size: 1.2rem;
                }}
                
                p {{
                    margin: 15px 0;
                    color: var(--text-secondary);
                }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 25px 0;
                    background: var(--bg-tertiary);
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                }}
                
                th {{
                    background: var(--primary-color);
                    color: white;
                    padding: 15px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 1rem;
                }}
                
                td {{
                    padding: 12px 15px;
                    border-bottom: 1px solid var(--border-color);
                    color: var(--text-secondary);
                }}
                
                tr:hover td {{
                    background: rgba(30, 136, 229, 0.1);
                    color: var(--text-primary);
                }}
                
                code {{
                    background: var(--bg-tertiary);
                    color: #ff6b6b;
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-family: 'Courier New', monospace;
                    font-size: 0.9em;
                    border: 1px solid var(--border-color);
                }}
                
                pre {{
                    background: var(--bg-tertiary);
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    padding: 20px;
                    overflow-x: auto;
                    margin: 20px 0;
                }}
                
                pre code {{
                    background: none;
                    border: none;
                    padding: 0;
                    color: #a8dadc;
                }}
                
                blockquote {{
                    border-left: 4px solid var(--primary-color);
                    background: rgba(30, 136, 229, 0.1);
                    padding: 15px 20px;
                    margin: 20px 0;
                    border-radius: 0 8px 8px 0;
                    color: var(--text-primary);
                    font-style: italic;
                }}
                
                ul, ol {{
                    padding-left: 25px;
                    margin: 15px 0;
                }}
                
                li {{
                    margin: 8px 0;
                    color: var(--text-secondary);
                }}
                
                strong {{
                    color: var(--primary-color);
                    font-weight: 600;
                }}
                
                em {{
                    color: var(--accent-color);
                }}
                
                hr {{
                    border: none;
                    height: 2px;
                    background: linear-gradient(
                        to right, 
                        transparent, 
                        var(--primary-color), 
                        transparent
                    );
                    margin: 40px 0;
                }}
                
                .footer {{
                    text-align: center;
                    padding: 30px;
                    background: var(--bg-tertiary);
                    margin-top: 40px;
                    border-radius: 10px;
                    border-top: 3px solid var(--primary-color);
                    color: var(--text-secondary);
                }}
                
                .toc {{
                    background: var(--bg-tertiary);
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                }}
                
                .toc h2 {{
                    margin-top: 0;
                    color: var(--primary-color);
                }}
                
                .toc ul {{
                    list-style-type: none;
                    padding-left: 0;
                }}
                
                .toc a {{
                    color: var(--accent-color);
                    text-decoration: none;
                    transition: color 0.3s;
                }}
                
                .toc a:hover {{
                    color: var(--primary-color);
                }}
                
                /* Scrollbar personalizada */
                ::-webkit-scrollbar {{
                    width: 12px;
                }}
                
                ::-webkit-scrollbar-track {{
                    background: var(--bg-primary);
                }}
                
                ::-webkit-scrollbar-thumb {{
                    background: var(--primary-color);
                    border-radius: 6px;
                }}
                
                ::-webkit-scrollbar-thumb:hover {{
                    background: var(--secondary-color);
                }}
                
                /* Animações */
                @keyframes fadeIn {{
                    from {{ opacity: 0; transform: translateY(20px); }}
                    to {{ opacity: 1; transform: translateY(0); }}
                }}
                
                .container {{
                    animation: fadeIn 0.6s ease-out;
                }}
                
                /* Responsividade */
                @media (max-width: 768px) {{
                    .container {{
                        margin: 10px;
                        padding: 20px;
                    }}
                    
                    .header h1 {{
                        font-size: 2rem;
                    }}
                    
                    table {{
                        font-size: 0.9rem;
                    }}
                    
                    th, td {{
                        padding: 8px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                {html}
            </div>
            
            <div class="footer">
                <p>
                    📞 <strong>Suporte:</strong> ti@oficialsport.com.br | 
                    📅 <strong>Versão:</strong> 1.0 | 
                    ©️ <strong>Oficial Sport</strong>
                </p>
            </div>
        </body>
        </html>
        """

    def basic_markdown_to_html(self, content):
        """
        Conversão básica de markdown para HTML
        """
        # Substituições básicas
        content = content.replace("\n# ", "\n<h1>")
        content = content.replace("\n## ", "\n<h2>")
        content = content.replace("\n### ", "\n<h3>")
        content = content.replace("\n#### ", "\n<h4>")
        content = content.replace("**", "<strong>").replace("**", "</strong>")
        content = content.replace("*", "<em>").replace("*", "</em>")
        content = content.replace("`", "<code>").replace("`", "</code>")
        content = content.replace("\n", "<br>")
        content = content.replace("---", "<hr>")

        return content


def start_manual_server():
    """
    Inicia servidor HTTP para servir o manual
    """
    PORT = 8888

    try:
        with socketserver.TCPServer(("", PORT), ManualHTTPRequestHandler) as httpd:
            print(f"Servidor do manual iniciado em http://localhost:{PORT}/manual")
            httpd.serve_forever()
    except OSError:
        # Porta em uso, tentar outra
        PORT = 8889
        try:
            with socketserver.TCPServer(("", PORT), ManualHTTPRequestHandler) as httpd:
                print(f"Servidor do manual iniciado em http://localhost:{PORT}/manual")
                httpd.serve_forever()
        except Exception as e:
            print(f"Erro ao iniciar servidor: {e}")


def open_manual_in_browser():
    """
    Abre o manual no navegador
    """
    # Iniciar servidor em thread separada
    server_thread = threading.Thread(target=start_manual_server, daemon=True)
    server_thread.start()

    # Aguardar um pouco para o servidor iniciar
    import time

    time.sleep(1)

    # Abrir no navegador
    webbrowser.open("http://localhost:8888/manual")


if __name__ == "__main__":
    open_manual_in_browser()
