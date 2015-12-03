//angular.module('routerApp')
myApp
		// 데이터 리스트 페이지
		.controller(
				'dataListCtrl',
				function($scope, $http, $stateParams, $location, $state, $rootScope) {
					// 리스트 검색
					$scope.search = function() {

						/**/
						$http
								.get('/data/jsonData')
								.success(
										function(dataList) {
											console.log('reload ' + $scope.pagingInfo.page);
											$scope.totalCnt = dataList.length;
											$scope.offset = ($scope.pagingInfo.page - 1)
													* $scope.pagingInfo.pagePerCnt;
											// console.log($scope.pagingInfo);
											
											// 로컬스토리지에 저장
											$scope.data = dataList;
											$location.search($scope.pagingInfo);								
										})
							/**/			
			
													
					}

					// 페이지 인포 객체가 없으면 한번 초기화
					/**/
					if(!$scope.pagingInfo){
						$scope.pagingInfo = {
								page : 1,
								totalCnt : null,
								pagePerCnt : 10

							};
						var obj = $location.search();
						$scope.pagingInfo.page = obj.page;
						$scope.search();
						
					}
					
					/**/
					
					// 페이징아 놀자
					$scope.$emit('paging', $scope);

					// 페이징 버튼 클릭시 이벤트
					$scope.pageChanged = function() {
					
						console.log('pageCanged')
						// console.log('query ' + $scope.query);
						$scope.search();
					};

				})
		// 상세보기 페이지
		.controller('dataDetailCtrl',
				function($scope, $http, $stateParams, $location) {

					$scope.page 	= $stateParams.page;
					$scope.offset 	= $stateParams.offset;
					$scope.query 	= $stateParams.query;

					var id = $stateParams.id;
					$http.get('/data/jsonData').success(function(dataList) {
						var data;

						for ( var prop in dataList) {
							if (dataList[prop]['_id'] == id) {
								data = dataList[prop];
							}
						}

						$scope.info = data;
					})

				})
		// url : /home
		.controller('homeDemoCtrl', function($scope, $uibModal, $log) {

			$scope.items = [ 'item1', 'item2', 'item3' ];

			$scope.animationsEnabled = true;

			$scope.open = function(size) {

				var modalInstance = $uibModal.open({
					animation 	: $scope.animationsEnabled,
					templateUrl : 'myModalContent.html',
					controller 	: 'ModalInstanceCtrl',
					size : size,
					resolve : {
						items : function() {
							return $scope.items;
						}
					}
				});

				modalInstance.result.then(function(selectedItem) {
					$scope.selected = selectedItem;
				}, function() {
					$log.info('Modal dismissed at: ' + new Date());
				});
			};

			$scope.toggleAnimation = function() {
				$scope.animationsEnabled = !$scope.animationsEnabled;
			};

		}).controller('ModalInstanceCtrl',
				function($scope, $uibModalInstance, items) {

					$scope.items = items;
					$scope.selected = {
						item : $scope.items[0]
					};

					$scope.ok = function() {
						$uibModalInstance.close($scope.selected.item);
					};

					$scope.cancel = function() {
						$uibModalInstance.dismiss('cancel');
					};

					// 페이징 처리
				}).controller('PaginationDemoCtrl', function($scope, $log) {
			// 난 페이징 이란 넘이얌
			$scope.$on('paging', function(event, $scope) {
			});

			// console.log($scope.pagingInfo);

		});
