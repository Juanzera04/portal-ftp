// endpoints base
const API = "https://ftp-backend1.onrender.com";
window.pendingLinks = [];
window.allGroups = [];
window.allClients = [];

// Função para mostrar notificações
function showNotification(message, type = 'info', duration = 3000) {
    // Remover notificação anterior se existir
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    
    const icon = type === 'success' ? '✅' : type === 'warning' ? '⚠️' : 'ℹ️';
    
    notification.innerHTML = `
        <span class="notification-icon">${icon}</span>
        ${message}
    `;
    
    document.body.appendChild(notification);
    
    // Animação de entrada
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Animação de saída
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 400);
    }, duration);
}

// carregar lista de grupos e renderizar cards
async function loadGroups() {
    const res = await fetch(`${API}/grupos`);
    const data = await res.json();
    
    window.allGroups = data;
    filterGroups();
}

// Filtra grupos baseado na pesquisa
function filterGroups() {
    const searchTerm = document.getElementById('searchGroups').value.toLowerCase();
    const filteredGroups = window.allGroups.filter(grupo => 
        grupo.toLowerCase().includes(searchTerm)
    );
    
    renderGroups(filteredGroups);
}

// Renderiza os grupos no container
function renderGroups(groups) {
    const container = document.getElementById("groupsContainer");
    container.innerHTML = "";

    if (groups.length === 0) {
        const noResults = document.createElement("div");
        noResults.className = "no-results";
        noResults.textContent = "Nenhum grupo encontrado";
        container.appendChild(noResults);
        return;
    }

    groups.forEach(grupo => {
        const card = document.createElement("div");
        card.className = "card";
        card.textContent = grupo;
        card.onclick = () => openClientsView(grupo);
        container.appendChild(card);
    });
}

// abre view dos clientes do grupo
async function openClientsView(grupo) {
    document.getElementById("groupsContainer").style.display = "none";
    document.querySelector(".topbar").style.display = "none";
    document.querySelector('.search-container').style.display = 'none';

    const clientsView = document.getElementById("clientsView");
    clientsView.style.display = "block";

    document.getElementById("groupName").textContent = grupo;

    const res = await fetch(`${API}/clientes/${encodeURIComponent(grupo)}`);
    const clientes = await res.json();
    
    window.allClients = clientes;
    filterClients();
}

// Filtra clientes baseado na pesquisa (nome ou ID)
function filterClients() {
    const searchTerm = document.getElementById('searchClients').value.toLowerCase();
    const filteredClients = window.allClients.filter(cliente => 
        cliente.nome.toLowerCase().includes(searchTerm) ||
        cliente.id.toLowerCase().includes(searchTerm)
    );
    
    renderClients(filteredClients);
}

// Renderiza os clientes no container
function renderClients(clients) {
    const clientsContainer = document.getElementById("clientsContainer");
    clientsContainer.innerHTML = "";

    if (clients.length === 0) {
        const noResults = document.createElement("div");
        noResults.className = "no-results";
        noResults.textContent = "Nenhum cliente encontrado";
        clientsContainer.appendChild(noResults);
        return;
    }

    clients.forEach(cliente => {
        const card = document.createElement("div");
        card.className = "card card-client";
        
        card.innerHTML = `
            <div class="client-name">${cliente.nome}</div>
            <div class="client-id">ID: ${cliente.id}</div>
        `;
        
        card.onclick = () => openClientView(cliente.nome);
        clientsContainer.appendChild(card);
    });
}

// abre view do cliente
async function openClientView(cliente) {
    document.getElementById("clientsView").style.display = "none";
    const view = document.getElementById("clientView");
    view.style.display = "block";

    document.getElementById("clientName").textContent = cliente;

    const res = await fetch(`${API}/categorias/${encodeURIComponent(cliente)}`);
    const categorias = await res.json();

    const categoryContainer = document.getElementById("categoryContainer");
    const filesContainer = document.getElementById("filesContainer");

    categoryContainer.innerHTML = "";
    filesContainer.innerHTML = "<em>Selecione uma categoria…</em>";

    window.selectedCategory = null;
    window.selectedDescription = null;
    window.selectedFilePath = null;

    // Carregar informações de quais categorias estão completas
    const categoriasCompletas = await checkCategoriasCompletas(cliente, categorias);

    categorias.forEach(cat => {
        const item = document.createElement("div");
        item.className = "category-item";
        
        const isCompleta = categoriasCompletas.includes(cat);
        
        if (isCompleta) {
            item.classList.add('completed');
        }
        
        const textSpan = document.createElement("span");
        textSpan.className = "category-text";
        textSpan.textContent = cat;
        item.appendChild(textSpan);
        
        item.onclick = () => toggleDescriptionsAndFiles(cliente, cat, item);
        categoryContainer.appendChild(item);
    });
}

// Verifica quais categorias estão completas (todas as descrições com arquivo)
async function checkCategoriasCompletas(cliente, categorias) {
    const categoriasCompletas = [];
    
    for (const categoria of categorias) {
        try {
            const resVinculos = await fetch(`${API}/vinculos/${encodeURIComponent(cliente)}/${encodeURIComponent(categoria)}`);
            if (resVinculos.ok) {
                const vinculos = await resVinculos.json();
                
                // Verificar se todas as descrições têm arquivo
                const todasComArquivo = vinculos.every(v => 
                    v.arquivo && v.arquivo.trim() !== ""
                );
                
                if (todasComArquivo && vinculos.length > 0) {
                    categoriasCompletas.push(categoria);
                }
            }
        } catch (error) {
            console.error(`Erro ao verificar categoria ${categoria}:`, error);
        }
    }
    
    return categoriasCompletas;
}

// expande/colapsa descrições e carrega arquivos
async function toggleDescriptionsAndFiles(cliente, categoria, element) {
    document.querySelectorAll('.category-item.selected').forEach(item => {
        item.classList.remove('selected');
    });
    
    element.classList.add('selected');
    window.selectedCategory = categoria;

    const existing = element.nextElementSibling;
    const filesContainer = document.getElementById("filesContainer");
    filesContainer.innerHTML = "<em>Carregando…</em>";

    if (existing && existing.classList.contains("desc-box")) {
        existing.remove();
        filesContainer.innerHTML = "<em>Selecione uma categoria…</em>";
        window.selectedCategory = null;
        element.classList.remove('selected');
        return;
    }

    try {
        const resDesc = await fetch(`${API}/descricoes/${encodeURIComponent(cliente)}/${encodeURIComponent(categoria)}`);
        if (!resDesc.ok) throw new Error('Erro ao carregar descrições');
        const descricoes = await resDesc.json();

        const resVinculos = await fetch(`${API}/vinculos/${encodeURIComponent(cliente)}/${encodeURIComponent(categoria)}`);
        let vinculos = [];
        if (resVinculos.ok) {
            vinculos = await resVinculos.json();
        }

        const box = document.createElement("div");
        box.className = "desc-box";

        if (!descricoes || descricoes.length === 0) {
            const none = document.createElement("div");
            none.className = "description-item";
            none.textContent = "(sem descrições)";
            box.appendChild(none);
        } else {
            descricoes.forEach(desc => {
                const item = document.createElement("div");
                item.className = "description-item";
                item.textContent = desc;
                
                const temArquivo = vinculos.some(v => 
                    v.descricao === desc && v.arquivo && v.arquivo.trim() !== ""
                );
                
                if (temArquivo) {
                    item.classList.add('completed');
                }
                
                item.onclick = () => selectDescription(desc, item);
                box.appendChild(item);
            });
        }

        element.insertAdjacentElement("afterend", box);
        await loadFilesForCategory(cliente, categoria);

    } catch (error) {
        console.error('Erro:', error);
        filesContainer.innerHTML = "<em>Erro ao carregar dados.</em>";
        
        const box = document.createElement("div");
        box.className = "desc-box";
        const errorItem = document.createElement("div");
        errorItem.className = "description-item";
        errorItem.textContent = "Erro ao carregar descrições";
        errorItem.style.color = "#ff6b6b";
        box.appendChild(errorItem);
        element.insertAdjacentElement("afterend", box);
    }
}

// selecionar descrição
function selectDescription(desc, element) {
    document.querySelectorAll('.description-item.selected').forEach(item => {
        item.classList.remove('selected');
    });
    
    element.classList.add('selected');
    window.selectedDescription = desc;
    updateDetailsFrame();
}

// carrega arquivos no lado direito
async function loadFilesForCategory(cliente, categoria) {
    try {
        const res = await fetch(`${API}/arquivos/${encodeURIComponent(cliente)}/${encodeURIComponent(categoria)}`);
        if (!res.ok) throw new Error('Erro ao carregar arquivos');
        const arquivos = await res.json();

        const right = document.getElementById("filesContainer");
        right.innerHTML = "";

        if (!arquivos || arquivos.length === 0) {
            right.innerHTML = "<em>Nenhum arquivo encontrado.</em>";
            return;
        }

        arquivos.forEach(a => {
            const item = document.createElement("div");
            item.className = "file-card";

            const title = document.createElement("div");
            title.textContent = a.ftp || a.nome || "(sem nome)";
            title.onclick = () => selectFile(a.caminho, item, title.textContent);
            item.appendChild(title);

            const copyBtn = document.createElement("button");
            copyBtn.className = "btn-copy";
            copyBtn.textContent = "Copiar";
            copyBtn.onclick = () => {
                navigator.clipboard.writeText(a.caminho);
                showNotification("Caminho copiado!", "success", 2000);
            };

            const openBtn = document.createElement("button");
            openBtn.className = "btn-open";
            openBtn.textContent = "Ver";
            openBtn.onclick = () => abrirArquivo(a.caminho);

            const actionBox = document.createElement("div");
            actionBox.className = "file-actions";
            actionBox.appendChild(copyBtn);
            actionBox.appendChild(openBtn);

            item.appendChild(actionBox);
            right.appendChild(item);
        });
    } catch (error) {
        console.error('Erro ao carregar arquivos:', error);
        const right = document.getElementById("filesContainer");
        right.innerHTML = "<em>Erro ao carregar arquivos.</em>";
    }
}

// selecionar arquivo
function selectFile(caminho, element, nomeArquivo) {
    document.querySelectorAll('.file-card.selected').forEach(item => {
        item.classList.remove('selected');
    });
    
    element.classList.add('selected');
    window.selectedFilePath = caminho;
    updateDetailsFrame();
}

// abrir arquivo
async function abrirArquivo(caminho) {
    const res = await fetch(`${API}/abrir_arquivo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ caminho })
    });

    if (!res.ok) {
        showNotification("Erro ao abrir arquivo.", "warning");
        return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
}

function updateDetailsFrame() {
    const frame = document.getElementById("detailsFrame");

    let descHTML = "";
    let fileHTML = "";

    if (window.selectedDescription) {
        descHTML = `
            <div class="detail-desc">
                <strong>Descrição selecionada:</strong><br>
                ${window.selectedDescription}
            </div>
        `;
    }

    if (window.selectedFilePath) {
        fileHTML = `
            <div class="detail-file">
                <strong>Arquivo selecionado:</strong><br>
                ${window.selectedFilePath}
            </div>
        `;
    }

    frame.innerHTML = descHTML + fileHTML;
}

// Navegação entre telas
function backToGroups() {
    document.getElementById("clientsView").style.display = "none";
    document.getElementById("groupsContainer").style.display = "grid";
    document.querySelector(".topbar").style.display = "flex";
    document.querySelector('.search-container').style.display = 'flex';
    window.pendingLinks = [];
    document.getElementById('searchClients').value = '';
}

function backToClients() {
    document.getElementById("clientView").style.display = "none";
    document.getElementById("clientsView").style.display = "block";
    window.pendingLinks = [];
}

document.addEventListener("DOMContentLoaded", () => {
    const linkButton = document.getElementById("linkButton");
    
    linkButton.onclick = () => {
        if (!window.selectedDescription || !window.selectedFilePath) {
            showNotification("Selecione uma descrição e um arquivo antes de linkar.", "warning");
            return;
        }

        const cliente = document.getElementById("clientName").textContent;

        window.pendingLinks.push({
            cliente: cliente,
            categoria: window.selectedCategory,
            descricao: window.selectedDescription,
            arquivo: window.selectedFilePath
        });

        showNotification("Link adicionado à lista pendente!", "success");
    };

    document.getElementById("backToGroups").onclick = backToGroups;

    document.getElementById("backToClients").onclick = async () => {
        if (window.pendingLinks.length === 0) {
            backToClients();
            return;
        }

        // Usar nossa nova notificação personalizada
        const confirmSave = await showConfirmNotification(
            `Você tem ${window.pendingLinks.length} links pendentes. Deseja salvar agora?`
        );

        if (!confirmSave) {
            backToClients();
            return;
        }

        try {
            const res = await fetch(`${API}/salvar_links`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(window.pendingLinks)
            });

            const data = await res.json();

            if (res.ok) {
                showNotification("Todos os links foram salvos com sucesso! ✅", "success", 4000);
            } else {
                showNotification("Erro ao salvar: " + data.erro, "warning");
            }
        } catch (error) {
            showNotification("Erro de conexão ao salvar links.", "warning");
        }

        backToClients();
    };

    // Event listeners para as barras de pesquisa
    document.getElementById('searchGroups').addEventListener('input', filterGroups);
    document.getElementById('searchClients').addEventListener('input', filterClients);

    // Focar na barra de pesquisa quando a tela carregar
    document.getElementById('searchGroups').focus();

});

// Função para notificação de confirmação personalizada
function showConfirmNotification(message) {
    return new Promise((resolve) => {
        const notification = document.createElement("div");
        notification.className = "notification warning";
        notification.innerHTML = `
            <div style="margin-bottom: 10px;">${message}</div>
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button id="confirmYes" style="padding: 5px 15px; background: #00ff88; border: none; border-radius: 5px; color: #000; font-weight: bold; cursor: pointer;">Sim</button>
                <button id="confirmNo" style="padding: 5px 15px; background: #ff6b6b; border: none; border-radius: 5px; color: white; font-weight: bold; cursor: pointer;">Não</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        document.getElementById('confirmYes').onclick = () => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 400);
            resolve(true);
        };
        
        document.getElementById('confirmNo').onclick = () => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 400);
            resolve(false);
        };
    });
}

// inicializa grupos
loadGroups();
