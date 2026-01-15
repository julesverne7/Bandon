let file_data_ds = null;

document.addEventListener("DOMContentLoaded", async function (event) {
    $("#excel_file_upload").on("change", async function (e) {
        let file = e.target.files[0];
        if (file) {
            let formData = new FormData();
            formData.append("file", file);
            const response = await fetch("/api/file/", {
                method: "POST",
                body: formData
            });
            if (response.ok) {
                const data = await response.json();
                notify_message("File uploaded successfully.", "success");
            } else {
                notify_message("File upload failed.", "error");
            }
            e.target.value = null;
        }
    });

    if (file_data_ds === null) {
        const file_response = await fetch("/api/file/", {
            method: "GET",
        });
        if (file_response.ok) {
            let file_data = await file_response.json();
            for (const element of file_data) {
                element.file_name = element.file.split("/").pop();
            }
            file_data_ds = new DevExpress.data.DataSource({
                store: {
                    type: "array",
                    data: file_data,
                    key: "id"
                },
            });
        }
    }
    const file_datagrid = $("#file-data-datagrid").dxDataGrid({
        dataSource: file_data_ds,
        pager: {
            showPageSizeSelector: true,
            allowedPageSizes: [25, 50, 100],
            showInfo: true,
        },
        paging: {
            pageSize: 25,
        },
        columns: [
            { dataField: "id", caption: "ID", width: 70 },
            { dataField: "file_name", caption: "File Name" },
            { dataField: "uploaded_at", caption: "Uploaded At", dataType: "datetime" },
            { dataField: "status", caption: "Status" },
            {
                caption: "Actions",
                type: "buttons",
                buttons: [
                    {
                        icon: "xlsxfile",
                        hint: "Download Reviewed File",
                        text: "Download Reviewed File",
                        onClick: function (e) {
                            window.location.href = `${e.row.data.results_excel}`;
                        }
                    },
                    {
                        icon: "pdffile",
                        hint: "Download Tables as PDF",
                        text: "Download Tables as PDF",
                        onClick: async function (e) {
                            await exportSchemasToPDF(e.row.data);
                        }
                    }
                ],
            }],
        masterDetail: {
            enabled: true,
            template: masterDetailTemplate,
        },
    }).dxDataGrid("instance");
});


function masterDetailTemplate(_, masterDetailOptions) {
    const data = masterDetailOptions.data;
    const items = [
        {
            title: 'Weighted Score',
            template: createTab1(data),
            index: 0,
        },
        {
            title: '% Sentiment',
            template: createTab2(data),
            index: 1,
        },
        {
            title: '% Reviews Mentioning',
            template: createTab3(data),
            index: 2,
        },
        {
            title: 'Sentiment By Location',
            template: createTab4(data),
            index: 3,
        },
        {
            title: 'Priority Matrix',
            template: createTab5(data),
            index: 4,
        },
    ];
    create_heatmap1(`#report-weighted-${data.id}`, masterDetailOptions.data.results);
    return $('<div>').dxTabPanel({
        items: items,
        onSelectionChanged: function (e) {
            setTimeout(() => {
                if (e.addedItems[0].index === 0) {
                    create_heatmap1(`#report-weighted-${data.id}`, data.results);
                } else if (e.addedItems[0].index === 1) {
                    // create_heatmap2(`#report-heatmap2-${data.id}`, data.results);
                    create_heatmap2(`#report-negative-sentiment-${data.id}`, data.results, "reds");
                    create_heatmap2(`#report-positive-sentiment-${data.id}`, data.results, "greens");
                }
                else if (e.addedItems[0].index === 2) {
                    create_heatmap3(`#report-heatmap3-${data.id}`, data.results);
                }
                else if (e.addedItems[0].index === 3) {
                    create_grouped_barchart(`#report-grouped-barchart1-${data.id}`, data.results, "Membership Billing");
                    create_grouped_barchart(`#report-grouped-barchart2-${data.id}`, data.results, "Equipment Quality");
                    create_grouped_barchart(`#report-grouped-barchart3-${data.id}`, data.results, "Customer Service");
                }
                else if (e.addedItems[0].index === 4) {
                    create_priority_matrix(`#report-priority-matrix-${data.id}`, data.results);
                }
            }, 100);
        }
    });

}

const notify_message = (message, type) => {
    // message: string, 
    // type: 'success', 'info', 'warning', 'error' 
    DevExpress.ui.notify({
        message: message,
        direction: 'up-push',
        position: 'bottom center',
        width: 450,
    }, type, 2000);
}

const create_heatmap1_schema = (data) => {
    // Calculate both positive and negative weighted scores
    let positiveResults = calculateWeightedScore(data, true);
    let negativeResults = calculateWeightedScore(data, false);

    let transformedData = [];

    // Combine positive and negative data
    positiveResults.locationNames.forEach((location, i) => {
        ['cleanliness', 'crowding', 'customer_service',
            'equipment_quality', 'membership_billing', 'price', 'staff_attitude'].forEach((category, j) => {
                transformedData.push({
                    location: location,
                    category: category,
                    sentiment: 'Positive',
                    intensity: positiveResults.data[i][j],
                });
                transformedData.push({
                    location: location,
                    category: category,
                    sentiment: 'Negative',
                    intensity: negativeResults.data[i][j],
                });
            });
    });

    let schema = {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "data": { "values": transformedData },
        "encoding": {
            "x": {
                "field": "category",
                "type": "ordinal",
                "sort": [
                    "cleanliness", "crowding", "customer_service",
                    "equipment_quality", "membership_billing", "price", "staff_attitude"
                ],
                "axis": { "title": "Category", "labelAngle": -90 }
            },
            "y": {
                "field": "location",
                "type": "ordinal",
                "axis": { "title": "Location" }
            },
            "xOffset": {
                "field": "sentiment",
                "type": "nominal",
                "sort": ["Positive", "Negative"]
            }
        },
        "layer": [
            {
                "mark": "rect",
                "transform": [
                    { "filter": "datum.sentiment === 'Positive'" }
                ],
                "encoding": {
                    "color": {
                        "aggregate": "mean",
                        "field": "intensity",
                        "type": "quantitative",
                        "scale": {
                            "domain": [0, 100],
                            "scheme": "greens",
                            "reverse": false
                        },
                        "legend": { "title": "Positive Score" }
                    },
                    "tooltip": [
                        { "field": "location", "title": "Location" },
                        { "field": "category", "title": "Category" },
                        { "field": "sentiment", "title": "Sentiment" },
                        { "aggregate": "mean", "field": "intensity", "title": "Score", "format": ".1f" },
                        { "aggregate": "count", "title": "# Reviews" }
                    ]
                }
            },
            {
                "mark": "rect",
                "transform": [
                    { "filter": "datum.sentiment === 'Negative'" }
                ],
                "encoding": {
                    "color": {
                        "aggregate": "mean",
                        "field": "intensity",
                        "type": "quantitative",
                        "scale": {
                            "domain": [0, 100],
                            "scheme": "reds",
                            "reverse": false
                        },
                        "legend": { "title": "Negative Score" }
                    },
                    "tooltip": [
                        { "field": "location", "title": "Location" },
                        { "field": "category", "title": "Category" },
                        { "field": "sentiment", "title": "Sentiment" },
                        { "aggregate": "mean", "field": "intensity", "title": "Score", "format": ".1f" },
                        { "aggregate": "count", "title": "# Reviews" }
                    ]
                }
            },
            {
                "mark": {
                    "type": "text",
                    "color": "black",
                    "fontSize": 9
                },
                "encoding": {
                    "text": {
                        "aggregate": "mean",
                        "field": "intensity",
                        "type": "quantitative",
                        "format": ".1f"
                    }
                }
            }
        ],
        "width": 800,
        "height": 120,
        "title": "Bandon Fitness - Weighted Positive vs Negative Score (% × Intensity)",
        "resolve": { "scale": { "color": "independent" } },
        "config": {
            "axis": { "grid": true, "tickBand": "extent" }
        }
    };
    return schema;
}

const create_heatmap1 = (div_id, data) => {
    vegaEmbed(div_id, create_heatmap1_schema(data), {
        actions: {
            export: false,
            source: false,
            compiled: false,
            editor: false
        }
    });
}

const create_heatmap2_schema = (data, color) => {
    // Transform flat data to array format for heatmap
    let is_positive = color === "greens";
    let results = calculateNegativePercentage(data, is_positive = is_positive);
    let transformedData = [];
    results.locationNames.forEach((location, i) => {
        ['cleanliness', 'crowding', 'customer_service',
            'equipment_quality', 'membership_billing', 'price', 'staff_attitude'].forEach((category, j) => {
                transformedData.push({
                    location: location,
                    category: category,
                    intensity: results.data[i][j],
                });
            });
    });
    let schema = {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "data": { "values": transformedData },
        "layer": [
            {
                "mark": "rect",
                "encoding": {
                    "x": {
                        "field": "category",
                        "type": "ordinal",
                        "sort": [
                            "cleanliness", "crowding", "customer_service",
                            "equipment_quality", "membership_billing", "price", "staff_attitude"
                        ],
                        "axis": { "title": "Category", "labelAngle": -90 }
                    },
                    "y": {
                        "field": "location",
                        "type": "ordinal",
                        "axis": { "title": "Location" }
                    },
                    "color": {
                        "aggregate": "mean",
                        "field": "intensity",
                        "type": "quantitative",
                        "scale": {
                            "domain": [0, 100],
                            "scheme": color,
                            "reverse": false
                        },
                        "legend": { "title": `${is_positive ? "Positive" : "Negative"} %` }
                    },
                    "tooltip": [
                        { "field": "location", "title": "Location" },
                        { "field": "category", "title": "Category" },
                        { "aggregate": "mean", "field": "intensity", "title": `${is_positive ? "Positive" : "Negative"} %`, "format": ".1f" },
                        { "aggregate": "count", "title": "# Reviews" }
                    ]
                }
            },
            {
                "mark": {
                    "type": "text",
                    "color": "black"
                },
                "encoding": {
                    "x": {
                        "field": "category",
                        "type": "ordinal"
                    },
                    "y": {
                        "field": "location",
                        "type": "ordinal"
                    },
                    "text": {
                        "aggregate": "mean",
                        "field": "intensity",
                        "type": "quantitative",
                        "format": ".1f"
                    }
                }
            }
        ],
        "width": 500,
        "height": 120,
        "title": `Bandon Fitness - % ${is_positive ? "Positive" : "Negative"} Sentiment by Location & Category`,
        "config": {
            "axis": { "grid": true, "tickBand": "extent" }
        }
    };
    return schema;
}

const create_heatmap2 = (div_id, data, color) => {
    vegaEmbed(div_id, create_heatmap2_schema(data, color), actions = {
        export: false,
        source: false,
        compiled: false,
        editor: false, action: false
    });
}

const create_heatmap3_schema = (data) => {
    // Transform flat data to array format for heatmap
    let results = calculateMentionFrequency(data);
    let transformedData = [];
    results.locationNames.forEach((location, i) => {
        ['cleanliness', 'crowding', 'customer_service',
            'equipment_quality', 'membership_billing', 'price', 'staff_attitude'].forEach((category, j) => {
                transformedData.push({
                    location: location,
                    category: category,
                    intensity: results.data[i][j],
                });
            });
    });
    let schema = {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "data": { "values": transformedData },
        "layer": [
            {
                "mark": "rect",
                "encoding": {
                    "x": {
                        "field": "category",
                        "type": "ordinal",
                        "sort": [
                            "cleanliness", "crowding", "customer_service",
                            "equipment_quality", "membership_billing", "price", "staff_attitude"
                        ],
                        "axis": { "title": "Category", "labelAngle": -45 }
                    },
                    "y": {
                        "field": "location",
                        "type": "ordinal",
                        "axis": { "title": "Location" }
                    },
                    "color": {
                        "aggregate": "mean",
                        "field": "intensity",
                        "type": "quantitative",
                        "scale": {
                            "domain": [0, 100],
                            "scheme": "redyellowgreen"
                        },
                        "legend": { "title": "Mention %" }
                    },
                    "tooltip": [
                        { "field": "location", "title": "Location" },
                        { "field": "category", "title": "Category" },
                        { "aggregate": "mean", "field": "intensity", "title": "Mention %", "format": ".1f" },
                        { "aggregate": "count", "title": "# Reviews" }
                    ]
                }
            },
            {
                "mark": {
                    "type": "text",
                    "color": "black"
                },
                "encoding": {
                    "x": {
                        "field": "category",
                        "type": "ordinal"
                    },
                    "y": {
                        "field": "location",
                        "type": "ordinal"
                    },
                    "text": {
                        "aggregate": "mean",
                        "field": "intensity",
                        "type": "quantitative",
                        "format": ".1f"
                    }
                }
            }
        ],
        "width": 600,
        "height": 400,
        "title": "Bandon Fitness - % Reviews Mentioning Each Category",
        "config": {
            "axis": { "grid": true, "tickBand": "extent" }
        }
    };
    return schema;
}

const create_heatmap3 = (div_id, data) => {
    vegaEmbed(div_id, create_heatmap3_schema(data), actions = {
        export: false,
        source: false,
        compiled: false,
        editor: false, action: false
    });
}

function createTab1(data) {
    return function (container) {
        // const $container = $('<div>').attr('id', `report-heatmap-${data.id}`);
        const $container = $('<div>')
        const $table = $('<table>').css({ 'width': '100%', 'border-collapse': 'collapse' });
        const $row = $('<tr>');
        const $cell1 = $('<td>').css({ 'width': '50%', 'padding': '10px' });
        const $div1 = $('<div>').attr('id', `report-weighted-${data.id}`);

        $cell1.append($div1);
        $row.append($cell1);
        $table.append($row);
        $container.append($table);

        return $container;
    };

}

function createTab2(data) {
    return function (container) {
        // const $container = $('<div>').attr('id', `report-heatmap-${data.id}`);
        const $container = $('<div>')
        const $table = $('<table>').css({ 'width': '100%', 'border-collapse': 'collapse' });
        const $row = $('<tr>');
        const $cell1 = $('<td>').css({ 'width': '50%', 'padding': '10px' });
        const $cell2 = $('<td>').css({ 'width': '50%', 'padding': '10px' });
        const $div1 = $('<div>').attr('id', `report-positive-sentiment-${data.id}`);
        const $div2 = $('<div>').attr('id', `report-negative-sentiment-${data.id}`);

        $cell1.append($div1);
        $cell2.append($div2);
        $row.append($cell1).append($cell2);
        $table.append($row);
        $container.append($table);

        return $container;
    };
}

function createTab3(data) {
    return function (container) {
        const $container = $('<div>').attr('id', `report-heatmap3-${data.id}`);

        return $container;
    };
}


function createTab4(data) {
    return function (container) {
        // const $container = $('<div>').attr('id', `report-heatmap-${data.id}`);
        const $container = $('<div>')
        const $table = $('<table>').css({ 'width': '100%', 'border-collapse': 'collapse' });
        const $row = $('<tr>');
        const $cell1 = $('<td>').css({ 'width': '33%', 'padding': '10px' });
        const $cell2 = $('<td>').css({ 'width': '33%', 'padding': '10px' });
        const $cell3 = $('<td>').css({ 'width': '33%', 'padding': '10px' });
        const $div1 = $('<div>').attr('id', `report-grouped-barchart1-${data.id}`);
        const $div2 = $('<div>').attr('id', `report-grouped-barchart2-${data.id}`);
        const $div3 = $('<div>').attr('id', `report-grouped-barchart3-${data.id}`);

        $cell1.append($div1);
        $cell2.append($div2);
        $cell3.append($div3);
        $row.append($cell1).append($cell2).append($cell3);
        $table.append($row);
        $container.append($table);

        return $container;
    };
}

function createTab5(data) {
    return function (container) {
        const $container = $('<div>').attr('id', `report-priority-matrix-${data.id}`);

        return $container;
    };
}

function calculateMentionFrequency(reviews) {
    /**
     * Calculate how often each category is mentioned (regardless of sentiment)
     * Returns: { data: 2D array, locationNames: array }
     */
    const categories = [
        'cleanliness', 'crowding', 'customer_service',
        'equipment_quality', 'membership_billing', 'price', 'staff_attitude'
    ];

    // Get unique locations
    const locations = [...new Set(reviews.map(r => r['PLACE ADDRESS'] || r.PLACE_ADDRESS))];

    const frequencyData = [];
    const locationNames = [];

    locations.forEach(location => {
        // Filter reviews for this location
        const locationReviews = reviews.filter(r =>
            (r['PLACE ADDRESS'] || r.PLACE_ADDRESS) === location
        );

        const rowData = [];

        // Extract city name from address for cleaner labels
        const city = location.includes(',')
            ? location.split(',')[1].trim()
            : location.substring(0, 30);
        locationNames.push(city);

        const totalReviews = locationReviews.length;

        categories.forEach(category => {
            const sentimentCol = `${category}_sentiment`;

            // Count non-neutral mentions
            const mentions = locationReviews.filter(r =>
                r[sentimentCol] !== 'neutral'
            ).length;

            // Calculate percentage
            const mentionPct = totalReviews > 0
                ? (mentions / totalReviews) * 100
                : 0;

            rowData.push(mentionPct);
        });

        frequencyData.push(rowData);
    });

    return { data: frequencyData, locationNames };
}


function calculateWeightedScore(reviews, is_positive = false) {
    /**
     * Calculate weighted negative score (percentage * intensity)
     * Returns: { data: 2D array, locationNames: array }
     */
    const categories = [
        'cleanliness', 'crowding', 'customer_service',
        'equipment_quality', 'membership_billing', 'price', 'staff_attitude'
    ];

    // Get unique locations
    const locations = [...new Set(reviews.map(r => r['PLACE ADDRESS'] || r.PLACE_ADDRESS))];

    const weightedData = [];
    const locationNames = [];

    locations.forEach(location => {
        // Filter reviews for this location
        const locationReviews = reviews.filter(r =>
            (r['PLACE ADDRESS'] || r.PLACE_ADDRESS) === location
        );

        const rowData = [];

        // Extract city name from address
        const city = location.includes(',')
            ? location.split(',')[1].trim()
            : location.substring(0, 30);
        locationNames.push(city);

        categories.forEach(category => {
            const sentimentCol = `${category}_sentiment`;
            const intensityCol = `${category}_intensity`;

            // Get negative reviews with their intensities
            const negativeReviews = locationReviews.filter(r =>
                r[sentimentCol] === (is_positive ? 'positive' : 'negative')
            );

            let weightedScore = 0;

            if (negativeReviews.length > 0) {
                // Calculate average intensity
                const intensities = negativeReviews.map(r => r[intensityCol]);
                const avgIntensity = intensities.reduce((a, b) => a + b, 0) / intensities.length;

                const negativeCount = negativeReviews.length;
                const totalReviews = locationReviews.length;

                // Weighted score: (% negative) * (avg intensity)
                weightedScore = (negativeCount / totalReviews * 100) * (avgIntensity / 5);
            }

            rowData.push(weightedScore);
        });

        weightedData.push(rowData);
    });

    return { data: weightedData, locationNames };
}



function calculateNegativePercentage(reviews, is_positive = false) {
    /**
     * Calculate percentage of negative mentions by location and category
     * Returns: { data: 2D array, locationNames: array }
     */
    const categories = [
        'cleanliness', 'crowding', 'customer_service',
        'equipment_quality', 'membership_billing', 'price', 'staff_attitude'
    ];

    // Get unique locations
    const locations = [...new Set(reviews.map(r => r['PLACE ADDRESS'] || r.PLACE_ADDRESS))];

    const heatmapData = [];
    const locationNames = [];

    locations.forEach(location => {
        // Filter reviews for this location
        const locationReviews = reviews.filter(r =>
            (r['PLACE ADDRESS'] || r.PLACE_ADDRESS) === location
        );

        const rowData = [];

        // Extract city name from address for cleaner labels
        const city = location.includes(',')
            ? location.split(',')[1].trim()
            : location.substring(0, 30);
        locationNames.push(city);

        categories.forEach(category => {
            const sentimentCol = `${category}_sentiment`;

            // Count mentions of this category (non-neutral)
            const totalMentions = locationReviews.filter(r =>
                r[sentimentCol] !== 'neutral'
            ).length;

            // Count negative mentions
            const negativeMentions = locationReviews.filter(r =>
                r[sentimentCol] === (is_positive ? 'positive' : 'negative')
            ).length;

            // Calculate percentage (avoid division by zero)
            const negativePct = totalMentions > 0
                ? (negativeMentions / totalMentions) * 100
                : 0;

            rowData.push(negativePct);
        });

        heatmapData.push(rowData);
    });

    return { data: heatmapData, locationNames };
}


const create_barchart1_schema = (data) => {
    /**
     * Create a bar chart showing number of reviews per location
     * Y-axis: Number of reviews
     * X-axis: Location
     */

    // Count reviews per location
    const locationCounts = {};

    data.forEach(review => {
        const location = review['PLACE ADDRESS'] || review.PLACE_ADDRESS;
        const city = location.includes(',')
            ? location.split(',')[1].trim()
            : location.substring(0, 30);

        if (!locationCounts[city]) {
            locationCounts[city] = 0;
        }
        locationCounts[city]++;
    });

    // Transform to array format
    const chartData = Object.entries(locationCounts).map(([location, count]) => ({
        location: location,
        count: count
    }));

    // Sort by count descending
    chartData.sort((a, b) => b.count - a.count);

    let schema = {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "data": { "values": chartData },
        "mark": {
            "type": "bar",
            "color": "#4682b4"
        },
        "width": 600,
        "height": 400,
        "title": "Number of Reviews by Location",
        "encoding": {
            "x": {
                "field": "location",
                "type": "ordinal",
                "axis": {
                    "title": "Location",
                    "labelAngle": -45
                },
                "sort": "-y"
            },
            "y": {
                "field": "count",
                "type": "quantitative",
                "axis": { "title": "Number of Reviews" }
            },
            "tooltip": [
                { "field": "location", "title": "Location" },
                { "field": "count", "title": "Number of Reviews" }
            ]
        },
        "config": {
            "axis": { "grid": true }
        }
    };
    return schema;
}

const create_barchart1 = (div_id, data) => {
    let schema = create_barchart1_schema(data);
    vegaEmbed(div_id, schema, actions = {
        export: false,
        source: false,
        compiled: false,
        editor: false, action: false
    });
}


const create_grouped_barchart_schema = (data, subject) => {
    /* Subject = Membership Billing, Equipment Quality, Customer Service 
    Create a grouped bar chart showing positive vs negative mentions by location for the given subject
    */

    // Convert subject to field name format (e.g., "Membership Billing" -> "membership_billing")
    const categoryField = subject.toLowerCase().replace(/\s+/g, '_');
    const sentimentField = `${categoryField}_sentiment`;

    // Get unique locations
    const locations = [...new Set(data.map(r => r['PLACE ADDRESS'] || r.PLACE_ADDRESS))];

    // Process data for each location
    const chartData = [];

    locations.forEach(location => {
        // Filter reviews for this location
        const locationReviews = data.filter(r =>
            (r['PLACE ADDRESS'] || r.PLACE_ADDRESS) === location
        );

        // Extract city name from address
        const city = location.includes(',')
            ? location.split(',')[1].trim()
            : location.substring(0, 30);

        // Count positive and negative mentions
        const positiveCount = locationReviews.filter(r =>
            r[sentimentField] === 'positive'
        ).length;

        const negativeCount = locationReviews.filter(r =>
            r[sentimentField] === 'negative'
        ).length;

        // Add data points for positive and negative
        chartData.push({
            location: city,
            sentiment: 'Positive',
            count: positiveCount
        });

        chartData.push({
            location: city,
            sentiment: 'Negative',
            count: negativeCount
        });
    });

    let schema = {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "data": { "values": chartData },
        "mark": "bar",
        "width": 300,
        "height": 200,
        "title": `${subject} - Sentiment by Location`,
        "encoding": {
            "x": {
                "field": "location",
                "type": "nominal",
                "axis": {
                    "title": "Location",
                    "labelAngle": -45
                }
            },
            "y": {
                "field": "count",
                "type": "quantitative",
                "axis": { "title": "Number of Mentions" }
            },
            "color": {
                "field": "sentiment",
                "type": "nominal",
                "scale": {
                    "domain": ["Positive", "Negative"],
                    "range": ["#2ecc71", "#e74c3c"]
                },
                "legend": { "title": "Sentiment" }
            },
            "xOffset": {
                "field": "sentiment"
            },
            "tooltip": [
                { "field": "location", "title": "Location" },
                { "field": "sentiment", "title": "Sentiment" },
                { "field": "count", "title": "Count" }
            ]
        },
        "config": {
            "axis": { "grid": true }
        }
    };
    return schema;
}


const create_grouped_barchart = (div_id, data, subject) => {
    let schema = create_grouped_barchart_schema(data, subject);
    vegaEmbed(div_id, schema, {
        actions: {
            export: false,
            source: false,
            compiled: false,
            editor: false
        }
    });
}

const create_priority_matrix_schema = (data) => {
    /**
     * Create a priority matrix bubble chart
     * X-axis: Frequency of Mentions (%)
     * Y-axis: % Negative When Mentioned
     * Bubble size: # of negative mentions
     */

    const categories = [
        { field: 'cleanliness', label: 'Cleanliness' },
        { field: 'crowding', label: 'Crowding' },
        { field: 'customer_service', label: 'Customer Service' },
        { field: 'equipment_quality', label: 'Equipment Quality' },
        { field: 'membership_billing', label: 'Membership Billing' },
        { field: 'price', label: 'Price' },
        { field: 'staff_attitude', label: 'Staff Attitude' }
    ];

    const chartData = [];
    const totalReviews = data.length;

    categories.forEach(category => {
        const sentimentField = `${category.field}_sentiment`;

        // Count mentions (non-neutral)
        const mentions = data.filter(r => r[sentimentField] !== 'neutral');
        const mentionCount = mentions.length;

        // Count negative mentions
        const negativeCount = data.filter(r => r[sentimentField] === 'negative').length;

        // Calculate metrics
        const frequencyPct = totalReviews > 0 ? (mentionCount / totalReviews) * 100 : 0;
        const negativePct = mentionCount > 0 ? (negativeCount / mentionCount) * 100 : 0;

        chartData.push({
            category: category.label,
            frequency: frequencyPct,
            negative_pct: negativePct,
            negative_count: negativeCount
        });
    });

    let schema = {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "data": { "values": chartData },
        "width": 700,
        "height": 500,
        "title": {
            "text": "Priority Matrix: Issue Frequency vs Negative Sentiment",
            "subtitle": "(Bubble size = # of negative mentions)",
            "fontSize": 16
        },
        "layer": [
            // Vertical line at x=40
            {
                "mark": {
                    "type": "rule",
                    "strokeDash": [4, 4],
                    "color": "#999",
                    "size": 1
                },
                "encoding": {
                    "x": { "datum": 40 }
                }
            },
            // Horizontal line at y=60
            {
                "mark": {
                    "type": "rule",
                    "strokeDash": [4, 4],
                    "color": "#999",
                    "size": 1
                },
                "encoding": {
                    "y": { "datum": 60 }
                }
            },
            // Bubbles
            {
                "mark": {
                    "type": "circle",
                    "opacity": 0.7,
                    "stroke": "#333",
                    "strokeWidth": 0.5
                },
                "encoding": {
                    "x": {
                        "field": "frequency",
                        "type": "quantitative",
                        "scale": { "domain": [0, 100] },
                        "axis": { "title": "Frequency of Mentions (%)", "grid": true }
                    },
                    "y": {
                        "field": "negative_pct",
                        "type": "quantitative",
                        "scale": { "domain": [0, 110] },
                        "axis": { "title": "% Negative When Mentioned", "grid": true }
                    },
                    "size": {
                        "field": "negative_count",
                        "type": "quantitative",
                        "scale": {
                            "type": "sqrt",
                            "range": [1000, 8000]
                        },
                        "legend": null
                    },
                    "color": {
                        "field": "negative_pct",
                        "type": "quantitative",
                        "scale": {
                            "type": "linear",
                            "domain": [0, 50, 100],
                            "range": ["#4caf50", "#ffeb3b", "#c62828"]
                        },
                        "legend": {
                            "title": "% Negative",
                            "orient": "right",
                            "gradientLength": 200
                        }
                    },
                    "tooltip": [
                        { "field": "category", "title": "Category" },
                        { "field": "frequency", "title": "Frequency %", "format": ".1f" },
                        { "field": "negative_pct", "title": "% Negative", "format": ".1f" },
                        { "field": "negative_count", "title": "# Negative Mentions" }
                    ]
                }
            },
            // Labels
            {
                "mark": {
                    "type": "text",
                    "dy": -20,
                    "fontSize": 10,
                    "fontWeight": "bold"
                },
                "encoding": {
                    "x": {
                        "field": "frequency",
                        "type": "quantitative"
                    },
                    "y": {
                        "field": "negative_pct",
                        "type": "quantitative"
                    },
                    "text": {
                        "field": "category",
                        "type": "nominal"
                    }
                }
            },
            // White background for HIGH PRIORITY text
            {
                "mark": {
                    "type": "rect",
                    "fill": "white",
                    "stroke": "#c62828",
                    "strokeWidth": 1,
                    "opacity": 1
                },
                "encoding": {
                    "x": { "datum": 86 },
                    "x2": { "datum": 100 },
                    "y": { "datum": 100 },
                    "y2": { "datum": 105 }
                }
            },
            // High priority text   
            {
                "mark": {
                    "name": "high-priority-text",
                    "type": "text",
                    "text": "HIGH PRIORITY",
                    "fontSize": 12,
                    "fontWeight": "bold",
                    "color": "#c62828",
                    "align": "right",
                    "baseline": "bottom",
                    "dx": -5,
                    "dy": -3
                },
                "encoding": {
                    "x": { "datum": 100 },
                    "y": { "datum": 100 }
                }
            },
        ],
        "config": {
            "view": {
                "stroke": "#ddd",
                "strokeWidth": 1
            },
            "background": "#fafafa"
        }
    };
    return schema;
}

const create_priority_matrix = (div_id, data) => {
    let schema = create_priority_matrix_schema(data);
    vegaEmbed(div_id, schema, {
        actions: {
            export: true,
            source: false,
            compiled: false,
            editor: false
        }
    });
}

async function exportSchemasToPDF(data) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    let yOffset = 10;

    const addChartToDoc = async (schema, title) => {
        // Create an off-screen temporary div
        const tempDiv = document.createElement('div');
        tempDiv.style.position = 'absolute';
        tempDiv.style.left = '-9999px';
        document.body.appendChild(tempDiv);

        try {
            // vegaEmbed handles Vega-Lite -> Vega compilation automatically
            const result = await vegaEmbed(tempDiv, schema, {
                actions: false,
                renderer: 'canvas', // Canvas required for reliable image export
                config: { background: 'white' } // Ensure not transparent
            });

            const view = result.view;
            const imageUrl = await view.toImageURL('png', 2); // 2x scale

            view.finalize(); // Cleanup
            document.body.removeChild(tempDiv);

            // Add new page if we are at bottom
            if (yOffset > 250) {
                doc.addPage();
                yOffset = 10;
            }

            doc.setFontSize(14);
            doc.text(title, 10, yOffset);
            yOffset += 10;

            // Calculate aspect ratio to fit PDF width (minus margins)
            const imgProps = doc.getImageProperties(imageUrl);
            const pdfImgWidth = pageWidth - 20;
            const pdfImgHeight = (imgProps.height * pdfImgWidth) / imgProps.width;

            doc.addImage(imageUrl, 'PNG', 10, yOffset, pdfImgWidth, pdfImgHeight);
            yOffset += pdfImgHeight + 10;

        } catch (err) {
            console.error(`Error rendering chart "${title}" for PDF:`, err);
            if (tempDiv.parentNode) document.body.removeChild(tempDiv);
        }
    };

    try {
        // 1. Weighted Score
        await addChartToDoc(create_heatmap1_schema(data.results), "Weighted Score");

        // 2. Sentiments
        await addChartToDoc(create_heatmap2_schema(data.results, "greens"), "Positive Sentiment %");
        await addChartToDoc(create_heatmap2_schema(data.results, "reds"), "Negative Sentiment %");

        // 3. Mentions
        await addChartToDoc(create_heatmap3_schema(data.results), "Review Mentions");

        doc.addPage();
        yOffset = 10;

        // 4. Bar Charts
        await addChartToDoc(create_grouped_barchart_schema(data.results, "Membership Billing"), "Membership Billing Sentiment");
        await addChartToDoc(create_grouped_barchart_schema(data.results, "Equipment Quality"), "Equipment Quality Sentiment");
        await addChartToDoc(create_grouped_barchart_schema(data.results, "Customer Service"), "Customer Service Sentiment");

        doc.addPage();
        yOffset = 10;

        // 5. Priority Matrix
        await addChartToDoc(create_priority_matrix_schema(data.results), "Priority Matrix");

        doc.save(`Report_${data.file_name}.pdf`);
        notify_message("PDF Downloaded successfully.", "success");
    } catch (e) {
        console.error("PDF Export Error: ", e);
        throw e;
    }
}