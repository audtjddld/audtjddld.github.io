var myApp = angular.module('routerApp', [ 'ui.router', 'ui.bootstrap',
		'ngAnimate' ]);


// 페이지 객체 불러오기
var pagingInfo = {
		page : 1,
		totalCnt : null,
		pagePerCnt : 10

	}
 

angular.module("template/pagination/pagination2.html", []).run(["$templateCache", function($templateCache) {
	  $templateCache.put("template/pagination/pagination.html",
	    "<ul class=\"pagination\">\n" +
	    "  <li ng-if=\"boundaryLinks\" ng-class=\"{disabled: noPrevious()}\"><a href=\"javascript:\" ng-click=\"selectPage(1, $event)\">{{getText('first')}}</a></li>\n" +
	    "  <li ng-if=\"directionLinks\" ng-class=\"{disabled: noPrevious()}\"><a href=\"javascript:\" ng-click=\"selectPage(page - 1, $event)\">{{getText('previous')}}</a></li>\n" +
	    "  <li ng-repeat=\"page in pages track by $index\" ng-class=\"{active: page.active}\"><a href=\"javascript:\" ng-click=\"selectPage(page.number, $event)\">{{page.text}}</a></li>\n" +
	    "  <li ng-if=\"directionLinks\" ng-class=\"{disabled: noNext()}\"><a href=\"javascript:\" ng-click=\"selectPage(page + 1, $event)\">{{getText('next')}}</a></li>\n" +
	    "  <li ng-if=\"boundaryLinks\" ng-class=\"{disabled: noNext()}\"><a href=\"javascript:\" ng-click=\"selectPage(totalPages, $event)\">{{getText('last')}}</a></li>\n" +
	    "</ul>");
	}]);
