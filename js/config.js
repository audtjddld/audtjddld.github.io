var myApp = angular.module('routerApp', [ 'ui.router', 'ui.bootstrap',
		'ngAnimate' ]);


// 페이지 객체 불러오기
var pagingInfo = {
		page : 1,
		totalCnt : null,
		pagePerCnt : 10

	}
