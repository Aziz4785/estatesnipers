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

