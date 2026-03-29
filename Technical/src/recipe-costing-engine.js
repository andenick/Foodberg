/**
 * Recipe Costing Engine for Professional Kitchens
 * Calculates accurate recipe costs including yield, shrinkage, and labor
 * Follows industry-standard costing methodologies
 */

const fs = require('fs').promises;
const path = require('path');

class RecipeCostingEngine {
  constructor() {
    // Standard yield percentages for common preparations
    this.standardYields = {
      // Proteins
      'beef_whole': 0.70, // 70% yield from whole primal
      'beef_trimmed': 0.85, // 85% yield from pre-trimmed
      'chicken_whole': 0.65, // 65% yield from whole chicken
      'chicken_breast': 0.95, // 95% yield from boneless breast
      'fish_whole': 0.45, // 45% yield from whole fish
      'fish_fillet': 0.90, // 90% yield from filleted fish
      'shrimp_shell_on': 0.65, // 65% yield after peeling
      'pork_whole': 0.72, // 72% yield from whole
      'lamb_whole': 0.68, // 68% yield from whole

      // Vegetables
      'onion': 0.87, // 87% yield after peeling
      'carrot': 0.82, // 82% yield after peeling/trimming
      'celery': 0.75, // 75% yield after trimming
      'potato': 0.81, // 81% yield after peeling
      'tomato': 0.95, // 95% yield (minimal loss)
      'lettuce': 0.76, // 76% yield after trimming
      'broccoli': 0.61, // 61% yield (florets only)
      'cauliflower': 0.55, // 55% yield (florets only)
      'bell_pepper': 0.82, // 82% yield after coring
      'mushroom': 0.90, // 90% yield after trimming

      // Fruits
      'apple': 0.76, // 76% yield after coring
      'orange': 0.70, // 70% yield for segments
      'lemon': 0.45, // 45% yield for juice
      'avocado': 0.65, // 65% yield after pit/skin
      'strawberry': 0.87, // 87% yield after hulling
      'pineapple': 0.50, // 50% yield after peeling/coring
    };

    // Cooking loss percentages
    this.cookingLoss = {
      'grilling': 0.25, // 25% moisture loss
      'roasting': 0.20, // 20% moisture loss
      'braising': 0.30, // 30% reduction
      'sauteing': 0.15, // 15% moisture loss
      'steaming': 0.05, // 5% minimal loss
      'poaching': 0.10, // 10% loss
      'frying': 0.20, // 20% moisture loss
      'raw': 0 // No cooking loss
    };

    // Standard portion sizes (in ounces)
    this.standardPortions = {
      'protein_main': 6, // 6 oz protein for main course
      'protein_appetizer': 3, // 3 oz for appetizer
      'starch': 4, // 4 oz starch
      'vegetable': 3, // 3 oz vegetable
      'salad': 2, // 2 oz salad greens
      'sauce': 2, // 2 oz sauce
      'garnish': 0.5 // 0.5 oz garnish
    };
  }

  /**
   * Calculate the cost of a single ingredient
   */
  calculateIngredientCost(ingredient) {
    const {
      name,
      quantity,
      unit,
      purchasePrice,
      purchaseUnit,
      yieldPercent = 1.0,
      preparation = 'raw'
    } = ingredient;

    // Convert units if necessary
    const quantityInPurchaseUnits = this.convertUnit(quantity, unit, purchaseUnit);

    // Calculate raw cost
    const rawCost = (quantityInPurchaseUnits * purchasePrice) / yieldPercent;

    // Apply cooking loss if applicable
    const cookingLossPercent = this.cookingLoss[preparation] || 0;
    const finalCost = rawCost * (1 + cookingLossPercent);

    return {
      name,
      rawCost: rawCost.toFixed(3),
      yieldLoss: ((1 - yieldPercent) * 100).toFixed(1),
      cookingLoss: (cookingLossPercent * 100).toFixed(1),
      finalCost: finalCost.toFixed(3),
      costPerUnit: (finalCost / quantity).toFixed(3)
    };
  }

  /**
   * Calculate total recipe cost including all factors
   */
  calculateRecipeCost(recipe) {
    const {
      name,
      yield: recipeYield = 1,
      ingredients = [],
      laborMinutes = 0,
      laborRate = 20, // Default $20/hour
      overheadPercent = 0.30, // 30% overhead default
      targetFoodCostPercent = 0.30 // 30% target food cost
    } = recipe;

    // Calculate ingredient costs
    const ingredientDetails = ingredients.map(ing => this.calculateIngredientCost(ing));
    const totalIngredientCost = ingredientDetails.reduce(
      (sum, ing) => sum + parseFloat(ing.finalCost), 0
    );

    // Calculate labor cost
    const laborCost = (laborMinutes / 60) * laborRate;

    // Calculate overhead
    const overheadCost = totalIngredientCost * overheadPercent;

    // Total cost
    const totalCost = totalIngredientCost + laborCost + overheadCost;

    // Cost per portion
    const costPerPortion = totalCost / recipeYield;

    // Suggested menu price based on target food cost percentage
    const suggestedMenuPrice = costPerPortion / targetFoodCostPercent;

    // Profit calculations
    const profitPerPortion = suggestedMenuPrice - costPerPortion;
    const profitMargin = (profitPerPortion / suggestedMenuPrice) * 100;

    return {
      recipeName: name,
      yield: recipeYield,
      ingredients: ingredientDetails,
      costs: {
        ingredients: totalIngredientCost.toFixed(2),
        labor: laborCost.toFixed(2),
        overhead: overheadCost.toFixed(2),
        total: totalCost.toFixed(2)
      },
      perPortion: {
        cost: costPerPortion.toFixed(2),
        suggestedPrice: suggestedMenuPrice.toFixed(2),
        profit: profitPerPortion.toFixed(2),
        foodCostPercent: (targetFoodCostPercent * 100).toFixed(1),
        profitMargin: profitMargin.toFixed(1)
      },
      analysis: this.generateCostAnalysis(costPerPortion, targetFoodCostPercent)
    };
  }

  /**
   * Generate cost analysis and recommendations
   */
  generateCostAnalysis(costPerPortion, targetFoodCost) {
    const analysis = {
      costLevel: '',
      recommendations: [],
      profitability: ''
    };

    // Determine cost level
    if (costPerPortion < 5) {
      analysis.costLevel = 'Low Cost';
      analysis.profitability = 'High Profit Potential';
    } else if (costPerPortion < 10) {
      analysis.costLevel = 'Moderate Cost';
      analysis.profitability = 'Good Profit Potential';
    } else if (costPerPortion < 20) {
      analysis.costLevel = 'Premium Cost';
      analysis.profitability = 'Premium Pricing Required';
    } else {
      analysis.costLevel = 'Luxury Cost';
      analysis.profitability = 'Luxury Market Positioning';
    }

    // Generate recommendations
    if (targetFoodCost > 0.35) {
      analysis.recommendations.push('Consider reducing portion sizes to improve margins');
      analysis.recommendations.push('Look for alternative suppliers for high-cost ingredients');
    }

    if (targetFoodCost < 0.25) {
      analysis.recommendations.push('Excellent cost control - consider premium presentation');
      analysis.recommendations.push('Opportunity to use higher quality ingredients');
    }

    return analysis;
  }

  /**
   * Calculate menu engineering matrix (popularity vs profitability)
   */
  calculateMenuEngineering(menuItems) {
    // Calculate averages
    const avgProfit = menuItems.reduce((sum, item) => sum + item.profit, 0) / menuItems.length;
    const avgSales = menuItems.reduce((sum, item) => sum + item.unitsSold, 0) / menuItems.length;

    // Classify each item
    const classified = menuItems.map(item => {
      let classification = '';

      if (item.profit >= avgProfit && item.unitsSold >= avgSales) {
        classification = 'STAR'; // High profit, high popularity
      } else if (item.profit >= avgProfit && item.unitsSold < avgSales) {
        classification = 'PUZZLE'; // High profit, low popularity
      } else if (item.profit < avgProfit && item.unitsSold >= avgSales) {
        classification = 'PLOW HORSE'; // Low profit, high popularity
      } else {
        classification = 'DOG'; // Low profit, low popularity
      }

      return {
        ...item,
        classification,
        action: this.getMenuAction(classification)
      };
    });

    return {
      items: classified,
      averages: {
        profit: avgProfit.toFixed(2),
        sales: avgSales.toFixed(0)
      },
      summary: this.generateMenuSummary(classified)
    };
  }

  /**
   * Get recommended action for menu item classification
   */
  getMenuAction(classification) {
    const actions = {
      'STAR': 'Maintain quality and promote actively',
      'PUZZLE': 'Increase marketing or reposition on menu',
      'PLOW HORSE': 'Increase price carefully or reduce portion cost',
      'DOG': 'Consider removing or complete rework'
    };

    return actions[classification] || 'Review item performance';
  }

  /**
   * Generate menu summary
   */
  generateMenuSummary(classifiedItems) {
    const counts = {
      STAR: 0,
      PUZZLE: 0,
      'PLOW HORSE': 0,
      DOG: 0
    };

    classifiedItems.forEach(item => {
      counts[item.classification]++;
    });

    return {
      distribution: counts,
      healthScore: this.calculateMenuHealth(counts),
      recommendations: this.generateMenuRecommendations(counts)
    };
  }

  /**
   * Calculate menu health score
   */
  calculateMenuHealth(counts) {
    const total = Object.values(counts).reduce((sum, count) => sum + count, 0);
    const starPercent = (counts.STAR / total) * 100;
    const dogPercent = (counts.DOG / total) * 100;

    if (starPercent > 30 && dogPercent < 20) {
      return 'Excellent';
    } else if (starPercent > 20 && dogPercent < 30) {
      return 'Good';
    } else if (starPercent > 10) {
      return 'Fair';
    } else {
      return 'Needs Improvement';
    }
  }

  /**
   * Generate menu recommendations
   */
  generateMenuRecommendations(counts) {
    const recommendations = [];

    if (counts.DOG > counts.STAR) {
      recommendations.push('Menu has too many underperforming items - consider menu reduction');
    }

    if (counts.PUZZLE > counts.STAR) {
      recommendations.push('Focus on marketing high-profit items to increase sales');
    }

    if (counts['PLOW HORSE'] > counts.STAR) {
      recommendations.push('Popular items have low margins - review pricing strategy');
    }

    if (counts.STAR < 2) {
      recommendations.push('Develop more high-profit, popular items');
    }

    return recommendations;
  }

  /**
   * Convert between units
   */
  convertUnit(quantity, fromUnit, toUnit) {
    // Simplified unit conversion (expand as needed)
    const conversions = {
      'lb_oz': 16,
      'kg_g': 1000,
      'gal_qt': 4,
      'qt_pt': 2,
      'pt_cup': 2,
      'cup_oz': 8,
      'tbsp_tsp': 3,
      'lb_g': 453.592,
      'oz_g': 28.3495
    };

    const conversionKey = `${fromUnit}_${toUnit}`;
    const reverseKey = `${toUnit}_${fromUnit}`;

    if (conversions[conversionKey]) {
      return quantity * conversions[conversionKey];
    } else if (conversions[reverseKey]) {
      return quantity / conversions[reverseKey];
    }

    // If no conversion found, return original quantity
    return quantity;
  }

  /**
   * Export recipe cost to Excel format
   */
  async exportToExcel(recipeData, filename = 'recipe_costs.csv') {
    const outputPath = path.join(__dirname, '..', '..', 'Output', 'Data', filename);

    let csv = 'Recipe Costing Report\n';
    csv += `Recipe Name: ${recipeData.recipeName}\n`;
    csv += `Yield: ${recipeData.yield} portions\n\n`;

    csv += 'Ingredient,Raw Cost,Yield Loss %,Cooking Loss %,Final Cost\n';

    recipeData.ingredients.forEach(ing => {
      csv += `"${ing.name}",${ing.rawCost},${ing.yieldLoss},${ing.cookingLoss},${ing.finalCost}\n`;
    });

    csv += '\nCost Summary\n';
    csv += `Ingredient Cost,$${recipeData.costs.ingredients}\n`;
    csv += `Labor Cost,$${recipeData.costs.labor}\n`;
    csv += `Overhead Cost,$${recipeData.costs.overhead}\n`;
    csv += `Total Cost,$${recipeData.costs.total}\n\n`;

    csv += 'Per Portion Analysis\n';
    csv += `Cost Per Portion,$${recipeData.perPortion.cost}\n`;
    csv += `Suggested Menu Price,$${recipeData.perPortion.suggestedPrice}\n`;
    csv += `Profit Per Portion,$${recipeData.perPortion.profit}\n`;
    csv += `Food Cost %,${recipeData.perPortion.foodCostPercent}%\n`;
    csv += `Profit Margin,${recipeData.perPortion.profitMargin}%\n`;

    await fs.writeFile(outputPath, csv);
    console.log(`Recipe cost exported to ${outputPath}`);

    return outputPath;
  }
}

// Export for use in other modules
module.exports = RecipeCostingEngine;

// Example usage
if (require.main === module) {
  (async () => {
    const costingEngine = new RecipeCostingEngine();

    // Example recipe: Grilled Chicken with Roasted Vegetables
    const recipe = {
      name: 'Grilled Chicken with Roasted Vegetables',
      yield: 10, // 10 portions
      ingredients: [
        {
          name: 'Chicken Breast',
          quantity: 4,
          unit: 'lb',
          purchasePrice: 3.99, // per pound
          purchaseUnit: 'lb',
          yieldPercent: 0.95,
          preparation: 'grilling'
        },
        {
          name: 'Broccoli',
          quantity: 2,
          unit: 'lb',
          purchasePrice: 2.49,
          purchaseUnit: 'lb',
          yieldPercent: 0.61,
          preparation: 'roasting'
        },
        {
          name: 'Carrots',
          quantity: 1.5,
          unit: 'lb',
          purchasePrice: 1.29,
          purchaseUnit: 'lb',
          yieldPercent: 0.82,
          preparation: 'roasting'
        },
        {
          name: 'Olive Oil',
          quantity: 4,
          unit: 'oz',
          purchasePrice: 0.25, // per oz
          purchaseUnit: 'oz',
          yieldPercent: 1.0,
          preparation: 'raw'
        },
        {
          name: 'Seasonings',
          quantity: 1,
          unit: 'oz',
          purchasePrice: 0.50,
          purchaseUnit: 'oz',
          yieldPercent: 1.0,
          preparation: 'raw'
        }
      ],
      laborMinutes: 30, // 30 minutes total labor
      laborRate: 20, // $20/hour
      overheadPercent: 0.30, // 30% overhead
      targetFoodCostPercent: 0.28 // 28% target food cost
    };

    console.log('Calculating recipe cost...\n');
    const recipeCost = costingEngine.calculateRecipeCost(recipe);
    console.log(JSON.stringify(recipeCost, null, 2));

    // Export to Excel
    await costingEngine.exportToExcel(recipeCost, 'grilled_chicken_cost.csv');

    // Example menu engineering
    const menuItems = [
      { name: 'Grilled Chicken', profit: 12.50, unitsSold: 150 },
      { name: 'Pasta Primavera', profit: 8.75, unitsSold: 95 },
      { name: 'Steak Frites', profit: 18.00, unitsSold: 75 },
      { name: 'Caesar Salad', profit: 6.50, unitsSold: 180 },
      { name: 'Lobster Risotto', profit: 22.00, unitsSold: 45 }
    ];

    console.log('\nMenu Engineering Analysis:');
    const menuAnalysis = costingEngine.calculateMenuEngineering(menuItems);
    console.log(JSON.stringify(menuAnalysis, null, 2));
  })();
}