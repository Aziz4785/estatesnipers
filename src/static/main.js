import { generateTable,positionOverlay,simulateClick,changeLegendTitle,updateLegend,showPremiumMessage,highlightFeature,openLoginModal,openChartModal} from './functions.js';
import { createSvgLineChart,openTab,getCurrentAreaId,setCurrentAreaId,layersByAreaId,getCurrentFillColor, setCurrentFillColor,getCurrentLegend, setCurrentLegend,applyGeoJSONLayer,map,chartDataMappings } from './app.js';

// Make changeLegendTitle globally available
window.changeLegendTitle = changeLegendTitle;
window.applyGeoJSONLayer = applyGeoJSONLayer;
window.updateLegend = updateLegend;
window.getCurrentFillColor = getCurrentFillColor;
window.setCurrentFillColor = setCurrentFillColor;
window.getCurrentLegend = getCurrentLegend;
window.setCurrentLegend = setCurrentLegend;
window.showPremiumMessage = showPremiumMessage;
window.highlightFeature = highlightFeature;
window.map = map;
window.openLoginModal = openLoginModal;
window.openChartModal = openChartModal;
window.chartDataMappings = chartDataMappings;
window.simulateClick = simulateClick;
window.layersByAreaId = layersByAreaId;
window.setCurrentAreaId = setCurrentAreaId;
window.getCurrentAreaId = getCurrentAreaId;
window.openTab = openTab;
window.generateTable = generateTable;
window.createSvgLineChart = createSvgLineChart;
window.positionOverlay = positionOverlay;

function clearCache() {
    if ('caches' in window) {
        caches.keys().then(function(names) {
            for (let name of names)
                caches.delete(name);
        });
    }
    window.location.reload(true);
}

// Call this function when you want to clear the cache and reload
// For example, you could call it when the page loads
window.onload = clearCache;