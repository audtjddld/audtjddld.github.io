package com.example.web;

import javax.servlet.http.HttpServletRequest;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
public class DemoController {
	
	/**
	 * 메인 페이지 이동
	 * @author 정명성
	 * create date : 2015. 12. 1.
	 * 설명
	 * @param request
	 * @return
	 */
	@RequestMapping(value="/")
	public String defaultPage(HttpServletRequest request ) {
		System.out.println("내가 탐");
		
		return "index";
	}

	/**
	 * 템플레이트 파일 맵핑
	 * @author 정명성
	 * create date : 2015. 12. 1.
	 * 설명
	 * @param request
	 * @param path1
	 * @param path2
	 * @param path3
	 * @return
	 */
	@RequestMapping(value="{1}/{2}/{3}.html")
	public String staticHtmlPage(HttpServletRequest request, 
										@PathVariable("1") String path1,
										@PathVariable("2") String path2,
										@PathVariable("3") String path3){
		
		return path1 + "/" +path2 + "/" +path3;
	}
	
	/**
	 * angular js에서 리프레쉬 할때 index페이지로 보내줌
	 * @author 정명성
	 * create date : 2015. 12. 1.
	 * 설명
	 * @param request
	 * @return
	 */
	//@RequestMapping(value="**")
	public String strangeUrlForwardIndex(HttpServletRequest request){
		System.out.println("@@@@");
		return "index";
	}
	
	/**
	 * 템플레이트 파일 맵핑
	 * @author 정명성
	 * create date : 2015. 12. 1.
	 * 설명
	 * @param request
	 * @param path1
	 * @param path2
	 * @param path3
	 * @return
	 */
	@RequestMapping(value="{1}/{2}.html")
	public String staticHtmlPage(HttpServletRequest request, 
										@PathVariable("1") String path1,
										@PathVariable("2") String path2){
		
		return path1 + "/" +path2;
	}
	
	/**
	 * 템플레이트 파일 맵핑
	 * @author 정명성
	 * create date : 2015. 12. 1.
	 * 설명
	 * @param request
	 * @param path1
	 * @param path2
	 * @param path3
	 * @return
	 */
	@RequestMapping(value="{1}.html")
	public String staticHtmlPage(HttpServletRequest request, 
										@PathVariable("1") String path1){
		
		return path1;
	}		
	
}
