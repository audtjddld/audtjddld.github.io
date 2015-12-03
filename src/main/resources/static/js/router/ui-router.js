myApp
	.config(function($locationProvider, $stateProvider, $urlRouterProvider) {
	
	// html5 모드
  $locationProvider.html5Mode(true).hashPrefix('!');
  $urlRouterProvider.otherwise("/");
  
  /*
  $urlRouterProvider.otherwise(function ($injector, $location) {
	    return '/';
  });
  */
  $stateProvider
	// index 라는 애는 url이 없고 view template 영역 중 2개를 변경한다..
    .state('home', {
				        url: "/home",
					  	templateUrl : '/myhome/home.html',
						controller: 'homeDemoCtrl'
    				}
      )
	// template 는 HTML String 
	// templateUrl 은 file Url      
     // 게시판
   .state('board', {
					   	//abstract: true,
					    url : "/board",
						templateUrl : '/myhome/board.html',
					    controller : 'dataListCtrl'	
		
    })
    // 상세보기
    .state('boardDetail',{
				    	url : "^/board/:id",
		    			templateUrl : '/myhome/board.detail.html',
		    			controller : 'dataDetailCtrl'				    	
    })      
    
});
