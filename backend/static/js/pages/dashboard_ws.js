function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const url = new URL(window.location.href);
    const socketUrl = `${protocol}://${url.host}/ws/`;
    const socket = new WebSocket(socketUrl);

    socket.onopen = function (event) {
        console.log('WebSocket is open now.');
    };

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        const file = JSON.parse(data.message);
        console.log('Processed file info:', file);
        if (file.status && file.id) {
            const arraystore = file_data_ds.store();
            arraystore.byKey(file.id)
                .done(function (item) {
                    item.status = file.status;
                    arraystore.update(item.id, item)
                        .done(function () {
                            file_data_ds.reload();
                            notify_message(`File ID ${item.id} processed: ${item.status}`, "info");
                        })
                        .fail(function (err) {
                            console.error('Error updating item:', err);
                        });
                })
                .fail(function (err) {
                    arraystore.push([{ type: "insert", data: file, index: file.id }]);
                    file_data_ds.reload();
                    notify_message(`File ID ${file.id} added: ${file.status}`, "info");
                });
        };
    }

    socket.onclose = function (event) {
        console.log('WebSocket is closed now.');
    };

    socket.onerror = function (error) {
        console.error('WebSocket error observed:', error);
    };
};

connectWebSocket();