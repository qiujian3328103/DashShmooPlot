var dagfuncs = window.dashAgGridFunctions = window.dashAgGridFunctions || {};

const tooltipRenderer = (params) => {
    const { yValue } = params;
    const sciValue = yValue.toExponential(2); // Convert to scientific notation with 2 decimal places
    return {
        title: 'Y Value',
        content: sciValue, // Show the scientific notation value as text
    };
}

dagfuncs.mySparklineRenderer = function(params) {
    // console.log(params);
    return {
        "sparklineOptions": {
            "type": "area",
            "marker": {
                "size": 2,
                "shape": "circle",
                "fill": "blue",
                "stroke": "blue",
                "strokeWidth": 2,
            },
            "fill": "rgba(216, 204, 235, 0.3)",
            "line": {
                "stroke": "rgb(119,77,185)",
            },
            "highlightStyle": {
                "fill": "rgb(143,185,77)",
            },
            "axis": {
                "stroke": "rgb(204, 204, 235)",
            },
            "crosshairs": {
                "xLine": {
                    "enabled": "true",
                    "lineDash": "dash",
                    "stroke": "rgba(0, 0, 0, 0.5)",
                },
                "yLine": {
                    "enabled": "true",
                    "lineDash": "dash",
                    "stroke": "rgba(0, 0, 0, 0.5)",
                },
            },
            "tooltip": {
                "enabled": true,
                "renderer": tooltipRenderer
            }
        }
    };
};
