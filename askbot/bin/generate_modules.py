<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" 
	"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
	<title>
	etienned / sphinx-autopackage-script / source &mdash; bitbucket.org
</title>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<meta name="description" content="Mercurial hosting - we're here to serve." />
	<meta name="keywords" content="mercurial,hg,hosting,bitbucket,etienned,This,script,parse,a,directory,tree,looking,for,python,modules,and,packages,and,create,ReST,files,appropriately,to,create,code,documentation,with,Sphinx.,It,also,create,a,modules,index.,source,sourcecode,generate_modules.py@d20aab0a12b8" />
	<link rel="stylesheet" type="text/css" href="http://bitbucket-assets.s3.amazonaws.com/css/layout.css" />
    <link rel="stylesheet" type="text/css" href="http://bitbucket-assets.s3.amazonaws.com/css/screen.css" />
	<link rel="stylesheet" type="text/css" href="http://bitbucket-assets.s3.amazonaws.com/css/print.css" media="print" />
	<link rel="search" type="application/opensearchdescription+xml" href="/opensearch.xml" title="Bitbucket" />
	<link rel="icon" href="http://bitbucket-assets.s3.amazonaws.com/img/logo_new.png" type="image/png"/>
	<script type="text/javascript">var MEDIA_URL = "http://bitbucket-assets.s3.amazonaws.com/"</script>
	<script type="text/javascript" src="http://bitbucket-assets.s3.amazonaws.com/js/lib/bundle.020510May.js"></script>
	
	<script type="text/javascript">
		$(document).ready(function() {
			Dropdown.init();
			$(".tooltip").tipsy({gravity:'s'});
		});
	</script>
	<noscript>
		<style type="text/css">
			.dropdown-container-text .dropdown {
				position: static !important;
			}
		</style>
	</noscript>

	<!--[if lt IE 7]>
	<style type="text/css">
	body {
		behavior: url(http://bitbucket-assets.s3.amazonaws.com/css/csshover.htc);
	}
	
	#issues-issue pre {
		white-space: normal !important;
	}
	
	.changeset-description {
		white-space: normal !important;
	}
	</style>
	<script type="text/javascript"> 
		$(document).ready(function(){ 
			$('#header-wrapper').pngFix();
			$('#sourcelist').pngFix();
			$('.promo-signup-screenshot').pngFix();
		}); 
	</script>
	<![endif]-->
	
	<link rel="stylesheet" href="http://bitbucket-assets.s3.amazonaws.com/css/highlight/trac.css" type="text/css" />

	
</head>
<body class="">
	<div id="main-wrapper">
		<div id="header-wrapper">
			<div id="header">
				<a href="/"><img src="http://bitbucket-assets.s3.amazonaws.com/img/logo_myriad.png" alt="Bitbucket" id="header-wrapper-logo" /></a>
				
					<div id="header-nav">
						<ul class="right">
							<li><a href="/">Home</a></li>
							<li><a href="/plans"><b>Plans &amp; Signup</b></a></li>
							<li><a href="/repo/all">Repositories</a></li>
							<li><a href="/news">News</a></li>
							<li><a href="/help">Help</a></li>
							<li><a href="/account/signin/">Sign in</a></li>
						</ul>
					</div>
				
			</div>
		</div>
		<div id="content-wrapper">
			
			
			

			
			
			
	
	





	<script type="text/javascript" src="http://bitbucket-assets.s3.amazonaws.com/js/lib/jquery.cookie.js"></script> <!--REMOVE WHEN NEWER BUNDLE THAN 030309Mar -->
	<script type="text/javascript">
		var date = new Date();
		date.setTime(date.getTime() + (365 * 24 * 60 * 60 * 1000));
		var cookieoptions = { path: '/', expires: date };
		
		window._shard = 'fe01 (ID 1)';
		
		$(document).ready(function(){
			$('#toggle-repo-content').click(function(){
				$('#repo-desc-cloneinfo').toggle('fast');
				$('#repo-menu').toggle();
				$('#repo-menu-links-mini').toggle(100);
				$('.repo-desc-description').toggle('fast');
				var avatar_new_width = ($('.repo-avatar').width() == 35) ? 16 : 35;
				$('.repo-avatar').animate({ width: avatar_new_width }, 250);
				
				if ($.cookie('toggle_status') == 'hide') {
					$.cookie('toggle_status', 'show', cookieoptions);
					$(this).css('background-image','url(http://bitbucket-assets.s3.amazonaws.com/img/repo-toggle-up.png)');
				} else {
					$.cookie('toggle_status', 'hide', cookieoptions);
					$(this).css('background-image','url(http://bitbucket-assets.s3.amazonaws.com/img/repo-toggle-down.png)');
				}
			});
			
			if ($.cookie('toggle_status') == 'hide') {
				$('#toggle-repo-content').css('background-image','url(http://bitbucket-assets.s3.amazonaws.com/img/repo-toggle-down.png)');
				$('#repo-desc-cloneinfo').hide();
				$('#repo-menu').hide();
				$('#repo-menu-links-mini').show();
				$('.repo-desc-description').hide();
				$('.repo-avatar').css({ width: '16px' });
			} else {
				$('#toggle-repo-content').css('background-image','url(http://bitbucket-assets.s3.amazonaws.com/img/repo-toggle-up.png)');
				$('#repo-desc-cloneinfo').show();
				$('#repo-menu').show();
				$('#repo-menu-links-mini').hide();
				$('.repo-desc-description').show();
				$('.repo-avatar').css({ width: '35px' });
			}
		});
	</script>


<div id="tabs">
	<ul class="ui-tabs-nav">
		<li>
			<a href="/etienned/sphinx-autopackage-script/overview"><span>Overview</span></a>
		</li>

		<li>
			<a href="/etienned/sphinx-autopackage-script/downloads"><span>Downloads (0)</span></a>
		</li>
		
		

		<li class="ui-tabs-selected">
			
				<a href="/etienned/sphinx-autopackage-script/src/d20aab0a12b8"><span>Source</span></a>
			
		</li>
		
		<li>
			<a href="/etienned/sphinx-autopackage-script/changesets"><span>Changesets</span></a>
		</li>

		
			
				<li class="ui-tabs-nav-issues">
					<a href="/etienned/sphinx-autopackage-script/wiki"><span>Wiki</span></a>
				</li>
			
		

		
			
				<li class="ui-tabs-nav-issues">
					<a href="/etienned/sphinx-autopackage-script/issues?status=new&amp;status=open"><span>Issues (1) &raquo;</span></a>
					<ul>
						<li><a href="/etienned/sphinx-autopackage-script/issues?status=new">New issues</a></li>
						<li><a href="/etienned/sphinx-autopackage-script/issues?status=new&amp;status=open">Open issues</a></li>
						<li><a href="/etienned/sphinx-autopackage-script/issues?status=resolved&amp;status=invalid&amp;status=duplicate">Closed issues</a></li>
					
						<li><a href="/etienned/sphinx-autopackage-script/issues">All issues</a></li>
						<li><a href="/etienned/sphinx-autopackage-script/issues/query">Advanced query</a></li>
						<li><a href="/etienned/sphinx-autopackage-script/issues/new">Create new issue</a></li>
					</ul>
				</li>
			
		
				
		
			
		
		
		<li class="tabs-right tabs-far-right">
			<a href="/etienned/sphinx-autopackage-script/descendants"><span>Forks/Queues (0)</span></a>
		</li>
		
		<li class="tabs-right">
			<a href="/etienned/sphinx-autopackage-script/zealots"><span>Followers (2)</span></a>
		</li>
	</ul>
</div>

<div id="repo-menu">
		<div id="repo-menu-links">
			<ul>
				<li>
					<a href="/etienned/sphinx-autopackage-script/rss" class="noborder repo-menu-rss" title="RSS Feed for sphinx-autopackage-script">RSS</a>
				</li>
				<li>
					<a href="/etienned/sphinx-autopackage-script/atom" class="noborder repo-menu-atom" title="Atom Feed for sphinx-autopackage-script">Atom</a>
				</li>
				
				<li>
					<a href="/etienned/sphinx-autopackage-script/pull" class="link-request-pull">
						pull request
					</a>
				</li>
				
				<li><a href="/etienned/sphinx-autopackage-script/fork" class="link-fork">fork</a></li>
				
					<li><a href="/etienned/sphinx-autopackage-script/hack" class="link-hack">patch queue</a></li>
				
				<li>
					
						<a rel="nofollow" href="/etienned/sphinx-autopackage-script/follow" class="link-follow">follow</a>
					
				</li>
				<li><a class="link-download">get source &raquo;</a>

					<ul>
						
							<li><a rel="nofollow" href="/etienned/sphinx-autopackage-script/get/d20aab0a12b8.zip" class="zip">zip</a></li>
							<li><a rel="nofollow" href="/etienned/sphinx-autopackage-script/get/d20aab0a12b8.gz" class="compressed">gz</a></li>
							<li><a rel="nofollow" href="/etienned/sphinx-autopackage-script/get/d20aab0a12b8.bz2" class="compressed">bz2</a></li>						
						
					</ul>
				</li>
			</ul>
		</div>
		
		
		<div id="repo-menu-branches-tags">
 			<ul>
				<li class="icon-branches">
					branches &raquo;
					
					<ul>
					
						<li><a href="/etienned/sphinx-autopackage-script/src/d20aab0a12b8">default</a></li>
					
					</ul>
					
				</li>
				<li class="icon-tags">
					tags &raquo;
					
					<ul>
					
						<li><a href="/etienned/sphinx-autopackage-script/src/d20aab0a12b8">tip</a></li>
					
					</ul>
				</li>
			</ul>
		</div>
		
		
		<div class="cb"></div>
	</div>
	<div id="repo-desc" class="layout-box">
		
		
		<div id="repo-menu-links-mini" class="right">
			<ul>
				<li>
					<a href="/etienned/sphinx-autopackage-script/rss" class="noborder repo-menu-rss" title="RSS Feed for sphinx-autopackage-script"></a>
				</li>
				<li>
					<a href="/etienned/sphinx-autopackage-script/atom" class="noborder repo-menu-atom" title="Atom Feed for sphinx-autopackage-script"></a>
				</li>
				
				<li>
					<a href="/etienned/sphinx-autopackage-script/pull" class="tooltip noborder link-request-pull" title="Pull request"></a>
				</li>
				
				<li><a href="/etienned/sphinx-autopackage-script/fork" class="tooltip noborder link-fork" title="Fork"></a></li>
				
					<li><a href="/etienned/sphinx-autopackage-script/hack" class="tooltip noborder link-hack" title="Patch queue"></a></li>
				
				<li><a class="tooltip noborder link-download" title="Get source"></a>

					<ul>
						
							<li><a rel="nofollow" href="/etienned/sphinx-autopackage-script/get/d20aab0a12b8.zip" class="zip">zip</a></li>
							<li><a rel="nofollow" href="/etienned/sphinx-autopackage-script/get/d20aab0a12b8.gz" class="compressed">gz</a></li>
							<li><a rel="nofollow" href="/etienned/sphinx-autopackage-script/get/d20aab0a12b8.bz2" class="compressed">bz2</a></li>						
						
					</ul>
				</li>
			</ul>
		</div>
		
		<h3>
			<a href="/etienned">etienned</a> / 
			<a href="/etienned/sphinx-autopackage-script">sphinx-autopackage-script</a>
			
			
		</h3>
		
		
		
		
		
		<p class="repo-desc-description">This script parse a directory tree looking for python modules and packages and
create ReST files appropriately to create code documentation with Sphinx.
It also create a modules index. </p>
		
		<div id="repo-desc-cloneinfo">Clone this repository (size: 5.8 KB): <a href="http://bitbucket.org/etienned/sphinx-autopackage-script" onclick="$('#clone-url-ssh').hide();$('#clone-url-https').toggle();return(false);"><small>HTTPS</small></a> / <a href="ssh://hg@bitbucket.org/etienned/sphinx-autopackage-script" onclick="$('#clone-url-https').hide();$('#clone-url-ssh').toggle();return(false);"><small>SSH</small></a><br/>
		<pre id="clone-url-https">$ hg clone <a href="http://bitbucket.org/etienned/sphinx-autopackage-script">http://bitbucket.org/etienned/sphinx-autopackage-script</a></pre>
		
		<pre id="clone-url-ssh" style="display:none;">$ hg clone <a href="ssh://hg@bitbucket.org/etienned/sphinx-autopackage-script">ssh://hg@bitbucket.org/etienned/sphinx-autopackage-script</a></pre></div>
		
		<div class="cb"></div>
		<a href="#" id="toggle-repo-content"></a>

		

	</div>


			
			





<div id="source-summary" class="layout-box">
	<div class="right">
		<table>
			<tr>
				<td>commit 0:</td>
				<td>d20aab0a12b8</td>
			</tr>
			
			
			<tr>
				<td>branch: </td>
				<td>default</td>
			</tr>
			
				<tr>
					<td>tags:</td>
					<td>tip</td>
				</tr>
			
		</table>
	</div>

<div class="changeset-description">Initial commit</div>
	
	<div>
		
			
				
					
<div class="dropdown-container">
	
		
			<img src="http://www.gravatar.com/avatar/6fc6e07b4af580b1424c082536570dd4?d=identicon&s=32" class="avatar dropdown" />
		
	
	
	<ul class="dropdown-list">
		<li>
			
				<a href="/etienne">View etienne's profile</a>
			
		</li>
		<li>
			<a href="">etienne's public repos &raquo;</a>
			
				
			
		</li>
		
			<li>
				<a href="/account/notifications/send/?receiver=etienne">Send message</a>
			</li>
		
	</ul>
</div>

				
			
		
			<span class="dropdown-right">
				
					
						<a href="/etienne">Etienne Lawlor</a> / 
					
					<a href="/etienne">etienne</a>
				
				<br/>
				<small class="dropdown-right">2 months ago</small>
			</span>
		
	</div>
				
	<div class="cb"></div>
</div>




<div id="source-path" class="layout-box">
	<a href="/etienned/sphinx-autopackage-script/src">sphinx-autopackage-script</a> /
	
		
			
				generate_modules.py
			
		
		
	
</div>


<div id="source-view" class="scroll-x">
	<table class="info-table">
		<tr>
			<th>r0:d20aab0a12b8</th>
			<th>287 loc</th>
			<th>10.7 KB</th>
			<th class="source-view-links">
				<a id="embed-link" href="#" onclick="makeEmbed('#embed-link', 'http://bitbucket.org/etienned/sphinx-autopackage-script/src/d20aab0a12b8/generate_modules.py?embed=t');">embed</a> /
				<a href='/etienned/sphinx-autopackage-script/history/generate_modules.py'>history</a> / 
				<a href='/etienned/sphinx-autopackage-script/annotate/d20aab0a12b8/generate_modules.py'>annotate</a> / 
				<a href='/etienned/sphinx-autopackage-script/raw/d20aab0a12b8/generate_modules.py'>raw</a> / 
				<form action="/etienned/sphinx-autopackage-script/diff/generate_modules.py" method="get" class="source-view-form">
					
					<select name='nothing' class="smaller" disabled="disabled">
						<option>No previous changes</option>
					</select>
					
				</form>
			</th>
		</tr>
	</table>
	
		
			<table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre><a href="#cl-1">  1</a>
<a href="#cl-2">  2</a>
<a href="#cl-3">  3</a>
<a href="#cl-4">  4</a>
<a href="#cl-5">  5</a>
<a href="#cl-6">  6</a>
<a href="#cl-7">  7</a>
<a href="#cl-8">  8</a>
<a href="#cl-9">  9</a>
<a href="#cl-10"> 10</a>
<a href="#cl-11"> 11</a>
<a href="#cl-12"> 12</a>
<a href="#cl-13"> 13</a>
<a href="#cl-14"> 14</a>
<a href="#cl-15"> 15</a>
<a href="#cl-16"> 16</a>
<a href="#cl-17"> 17</a>
<a href="#cl-18"> 18</a>
<a href="#cl-19"> 19</a>
<a href="#cl-20"> 20</a>
<a href="#cl-21"> 21</a>
<a href="#cl-22"> 22</a>
<a href="#cl-23"> 23</a>
<a href="#cl-24"> 24</a>
<a href="#cl-25"> 25</a>
<a href="#cl-26"> 26</a>
<a href="#cl-27"> 27</a>
<a href="#cl-28"> 28</a>
<a href="#cl-29"> 29</a>
<a href="#cl-30"> 30</a>
<a href="#cl-31"> 31</a>
<a href="#cl-32"> 32</a>
<a href="#cl-33"> 33</a>
<a href="#cl-34"> 34</a>
<a href="#cl-35"> 35</a>
<a href="#cl-36"> 36</a>
<a href="#cl-37"> 37</a>
<a href="#cl-38"> 38</a>
<a href="#cl-39"> 39</a>
<a href="#cl-40"> 40</a>
<a href="#cl-41"> 41</a>
<a href="#cl-42"> 42</a>
<a href="#cl-43"> 43</a>
<a href="#cl-44"> 44</a>
<a href="#cl-45"> 45</a>
<a href="#cl-46"> 46</a>
<a href="#cl-47"> 47</a>
<a href="#cl-48"> 48</a>
<a href="#cl-49"> 49</a>
<a href="#cl-50"> 50</a>
<a href="#cl-51"> 51</a>
<a href="#cl-52"> 52</a>
<a href="#cl-53"> 53</a>
<a href="#cl-54"> 54</a>
<a href="#cl-55"> 55</a>
<a href="#cl-56"> 56</a>
<a href="#cl-57"> 57</a>
<a href="#cl-58"> 58</a>
<a href="#cl-59"> 59</a>
<a href="#cl-60"> 60</a>
<a href="#cl-61"> 61</a>
<a href="#cl-62"> 62</a>
<a href="#cl-63"> 63</a>
<a href="#cl-64"> 64</a>
<a href="#cl-65"> 65</a>
<a href="#cl-66"> 66</a>
<a href="#cl-67"> 67</a>
<a href="#cl-68"> 68</a>
<a href="#cl-69"> 69</a>
<a href="#cl-70"> 70</a>
<a href="#cl-71"> 71</a>
<a href="#cl-72"> 72</a>
<a href="#cl-73"> 73</a>
<a href="#cl-74"> 74</a>
<a href="#cl-75"> 75</a>
<a href="#cl-76"> 76</a>
<a href="#cl-77"> 77</a>
<a href="#cl-78"> 78</a>
<a href="#cl-79"> 79</a>
<a href="#cl-80"> 80</a>
<a href="#cl-81"> 81</a>
<a href="#cl-82"> 82</a>
<a href="#cl-83"> 83</a>
<a href="#cl-84"> 84</a>
<a href="#cl-85"> 85</a>
<a href="#cl-86"> 86</a>
<a href="#cl-87"> 87</a>
<a href="#cl-88"> 88</a>
<a href="#cl-89"> 89</a>
<a href="#cl-90"> 90</a>
<a href="#cl-91"> 91</a>
<a href="#cl-92"> 92</a>
<a href="#cl-93"> 93</a>
<a href="#cl-94"> 94</a>
<a href="#cl-95"> 95</a>
<a href="#cl-96"> 96</a>
<a href="#cl-97"> 97</a>
<a href="#cl-98"> 98</a>
<a href="#cl-99"> 99</a>
<a href="#cl-100">100</a>
<a href="#cl-101">101</a>
<a href="#cl-102">102</a>
<a href="#cl-103">103</a>
<a href="#cl-104">104</a>
<a href="#cl-105">105</a>
<a href="#cl-106">106</a>
<a href="#cl-107">107</a>
<a href="#cl-108">108</a>
<a href="#cl-109">109</a>
<a href="#cl-110">110</a>
<a href="#cl-111">111</a>
<a href="#cl-112">112</a>
<a href="#cl-113">113</a>
<a href="#cl-114">114</a>
<a href="#cl-115">115</a>
<a href="#cl-116">116</a>
<a href="#cl-117">117</a>
<a href="#cl-118">118</a>
<a href="#cl-119">119</a>
<a href="#cl-120">120</a>
<a href="#cl-121">121</a>
<a href="#cl-122">122</a>
<a href="#cl-123">123</a>
<a href="#cl-124">124</a>
<a href="#cl-125">125</a>
<a href="#cl-126">126</a>
<a href="#cl-127">127</a>
<a href="#cl-128">128</a>
<a href="#cl-129">129</a>
<a href="#cl-130">130</a>
<a href="#cl-131">131</a>
<a href="#cl-132">132</a>
<a href="#cl-133">133</a>
<a href="#cl-134">134</a>
<a href="#cl-135">135</a>
<a href="#cl-136">136</a>
<a href="#cl-137">137</a>
<a href="#cl-138">138</a>
<a href="#cl-139">139</a>
<a href="#cl-140">140</a>
<a href="#cl-141">141</a>
<a href="#cl-142">142</a>
<a href="#cl-143">143</a>
<a href="#cl-144">144</a>
<a href="#cl-145">145</a>
<a href="#cl-146">146</a>
<a href="#cl-147">147</a>
<a href="#cl-148">148</a>
<a href="#cl-149">149</a>
<a href="#cl-150">150</a>
<a href="#cl-151">151</a>
<a href="#cl-152">152</a>
<a href="#cl-153">153</a>
<a href="#cl-154">154</a>
<a href="#cl-155">155</a>
<a href="#cl-156">156</a>
<a href="#cl-157">157</a>
<a href="#cl-158">158</a>
<a href="#cl-159">159</a>
<a href="#cl-160">160</a>
<a href="#cl-161">161</a>
<a href="#cl-162">162</a>
<a href="#cl-163">163</a>
<a href="#cl-164">164</a>
<a href="#cl-165">165</a>
<a href="#cl-166">166</a>
<a href="#cl-167">167</a>
<a href="#cl-168">168</a>
<a href="#cl-169">169</a>
<a href="#cl-170">170</a>
<a href="#cl-171">171</a>
<a href="#cl-172">172</a>
<a href="#cl-173">173</a>
<a href="#cl-174">174</a>
<a href="#cl-175">175</a>
<a href="#cl-176">176</a>
<a href="#cl-177">177</a>
<a href="#cl-178">178</a>
<a href="#cl-179">179</a>
<a href="#cl-180">180</a>
<a href="#cl-181">181</a>
<a href="#cl-182">182</a>
<a href="#cl-183">183</a>
<a href="#cl-184">184</a>
<a href="#cl-185">185</a>
<a href="#cl-186">186</a>
<a href="#cl-187">187</a>
<a href="#cl-188">188</a>
<a href="#cl-189">189</a>
<a href="#cl-190">190</a>
<a href="#cl-191">191</a>
<a href="#cl-192">192</a>
<a href="#cl-193">193</a>
<a href="#cl-194">194</a>
<a href="#cl-195">195</a>
<a href="#cl-196">196</a>
<a href="#cl-197">197</a>
<a href="#cl-198">198</a>
<a href="#cl-199">199</a>
<a href="#cl-200">200</a>
<a href="#cl-201">201</a>
<a href="#cl-202">202</a>
<a href="#cl-203">203</a>
<a href="#cl-204">204</a>
<a href="#cl-205">205</a>
<a href="#cl-206">206</a>
<a href="#cl-207">207</a>
<a href="#cl-208">208</a>
<a href="#cl-209">209</a>
<a href="#cl-210">210</a>
<a href="#cl-211">211</a>
<a href="#cl-212">212</a>
<a href="#cl-213">213</a>
<a href="#cl-214">214</a>
<a href="#cl-215">215</a>
<a href="#cl-216">216</a>
<a href="#cl-217">217</a>
<a href="#cl-218">218</a>
<a href="#cl-219">219</a>
<a href="#cl-220">220</a>
<a href="#cl-221">221</a>
<a href="#cl-222">222</a>
<a href="#cl-223">223</a>
<a href="#cl-224">224</a>
<a href="#cl-225">225</a>
<a href="#cl-226">226</a>
<a href="#cl-227">227</a>
<a href="#cl-228">228</a>
<a href="#cl-229">229</a>
<a href="#cl-230">230</a>
<a href="#cl-231">231</a>
<a href="#cl-232">232</a>
<a href="#cl-233">233</a>
<a href="#cl-234">234</a>
<a href="#cl-235">235</a>
<a href="#cl-236">236</a>
<a href="#cl-237">237</a>
<a href="#cl-238">238</a>
<a href="#cl-239">239</a>
<a href="#cl-240">240</a>
<a href="#cl-241">241</a>
<a href="#cl-242">242</a>
<a href="#cl-243">243</a>
<a href="#cl-244">244</a>
<a href="#cl-245">245</a>
<a href="#cl-246">246</a>
<a href="#cl-247">247</a>
<a href="#cl-248">248</a>
<a href="#cl-249">249</a>
<a href="#cl-250">250</a>
<a href="#cl-251">251</a>
<a href="#cl-252">252</a>
<a href="#cl-253">253</a>
<a href="#cl-254">254</a>
<a href="#cl-255">255</a>
<a href="#cl-256">256</a>
<a href="#cl-257">257</a>
<a href="#cl-258">258</a>
<a href="#cl-259">259</a>
<a href="#cl-260">260</a>
<a href="#cl-261">261</a>
<a href="#cl-262">262</a>
<a href="#cl-263">263</a>
<a href="#cl-264">264</a>
<a href="#cl-265">265</a>
<a href="#cl-266">266</a>
<a href="#cl-267">267</a>
<a href="#cl-268">268</a>
<a href="#cl-269">269</a>
<a href="#cl-270">270</a>
<a href="#cl-271">271</a>
<a href="#cl-272">272</a>
<a href="#cl-273">273</a>
<a href="#cl-274">274</a>
<a href="#cl-275">275</a>
<a href="#cl-276">276</a>
<a href="#cl-277">277</a>
<a href="#cl-278">278</a>
<a href="#cl-279">279</a>
<a href="#cl-280">280</a>
<a href="#cl-281">281</a>
<a href="#cl-282">282</a>
<a href="#cl-283">283</a>
<a href="#cl-284">284</a>
<a href="#cl-285">285</a>
<a href="#cl-286">286</a>
<a href="#cl-287">287</a>
<a href="#cl-288">288</a>
</pre></div></td><td class="code"><div class="highlight"><pre><a name="cl-1"></a><span class="c">#!/usr/bin/env python</span>
<a name="cl-2"></a><span class="c"># -*- coding: utf-8 -*-</span>
<a name="cl-3"></a>
<a name="cl-4"></a><span class="c"># Miville</span>
<a name="cl-5"></a><span class="c"># Copyright (C) 2008 Société des arts technologiques (SAT)</span>
<a name="cl-6"></a><span class="c"># http://www.sat.qc.ca</span>
<a name="cl-7"></a><span class="c"># All rights reserved.</span>
<a name="cl-8"></a><span class="c">#</span>
<a name="cl-9"></a><span class="c"># This file is free software: you can redistribute it and/or modify</span>
<a name="cl-10"></a><span class="c"># it under the terms of the GNU General Public License as published by</span>
<a name="cl-11"></a><span class="c"># the Free Software Foundation, either version 2 of the License, or</span>
<a name="cl-12"></a><span class="c"># (at your option) any later version.</span>
<a name="cl-13"></a><span class="c">#</span>
<a name="cl-14"></a><span class="c"># Miville is distributed in the hope that it will be useful,</span>
<a name="cl-15"></a><span class="c"># but WITHOUT ANY WARRANTY; without even the implied warranty of</span>
<a name="cl-16"></a><span class="c"># MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the</span>
<a name="cl-17"></a><span class="c"># GNU General Public License for more details.</span>
<a name="cl-18"></a><span class="c">#</span>
<a name="cl-19"></a><span class="c"># You should have received a copy of the GNU General Public License</span>
<a name="cl-20"></a><span class="c"># along with Miville.  If not, see &lt;http://www.gnu.org/licenses/&gt;.</span>
<a name="cl-21"></a>
<a name="cl-22"></a><span class="sd">&quot;&quot;&quot;</span>
<a name="cl-23"></a><span class="sd">This script parse a directory tree looking for python modules and packages and</span>
<a name="cl-24"></a><span class="sd">create ReST files appropriately to create code documentation with Sphinx.</span>
<a name="cl-25"></a><span class="sd">It also create a modules index. </span>
<a name="cl-26"></a><span class="sd">&quot;&quot;&quot;</span>
<a name="cl-27"></a>
<a name="cl-28"></a><span class="kn">import</span> <span class="nn">os</span>
<a name="cl-29"></a><span class="kn">import</span> <span class="nn">optparse</span>
<a name="cl-30"></a>
<a name="cl-31"></a>
<a name="cl-32"></a><span class="c"># automodule options</span>
<a name="cl-33"></a><span class="n">OPTIONS</span> <span class="o">=</span> <span class="p">[</span><span class="s">&#39;members&#39;</span><span class="p">,</span>
<a name="cl-34"></a>            <span class="s">&#39;undoc-members&#39;</span><span class="p">,</span>
<a name="cl-35"></a><span class="c">#            &#39;inherited-members&#39;, # disable because there&#39;s a bug in sphinx</span>
<a name="cl-36"></a>            <span class="s">&#39;show-inheritance&#39;</span><span class="p">]</span>
<a name="cl-37"></a>
<a name="cl-38"></a>
<a name="cl-39"></a><span class="k">def</span> <span class="nf">create_file_name</span><span class="p">(</span><span class="n">base</span><span class="p">,</span> <span class="n">opts</span><span class="p">):</span>
<a name="cl-40"></a>    <span class="sd">&quot;&quot;&quot;Create file name from base name, path and suffix&quot;&quot;&quot;</span>
<a name="cl-41"></a>    <span class="k">return</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">join</span><span class="p">(</span><span class="n">opts</span><span class="o">.</span><span class="n">destdir</span><span class="p">,</span> <span class="s">&quot;</span><span class="si">%s</span><span class="s">.</span><span class="si">%s</span><span class="s">&quot;</span> <span class="o">%</span> <span class="p">(</span><span class="n">base</span><span class="p">,</span> <span class="n">opts</span><span class="o">.</span><span class="n">suffix</span><span class="p">))</span>
<a name="cl-42"></a>
<a name="cl-43"></a><span class="k">def</span> <span class="nf">write_directive</span><span class="p">(</span><span class="n">module</span><span class="p">,</span> <span class="n">package</span><span class="o">=</span><span class="bp">None</span><span class="p">):</span>
<a name="cl-44"></a>    <span class="sd">&quot;&quot;&quot;Create the automodule directive and add the options&quot;&quot;&quot;</span>
<a name="cl-45"></a>    <span class="k">if</span> <span class="n">package</span><span class="p">:</span>
<a name="cl-46"></a>        <span class="n">directive</span> <span class="o">=</span> <span class="s">&#39;.. automodule:: </span><span class="si">%s</span><span class="s">.</span><span class="si">%s</span><span class="se">\n</span><span class="s">&#39;</span> <span class="o">%</span> <span class="p">(</span><span class="n">package</span><span class="p">,</span> <span class="n">module</span><span class="p">)</span>
<a name="cl-47"></a>    <span class="k">else</span><span class="p">:</span>
<a name="cl-48"></a>        <span class="n">directive</span> <span class="o">=</span> <span class="s">&#39;.. automodule:: </span><span class="si">%s</span><span class="se">\n</span><span class="s">&#39;</span> <span class="o">%</span> <span class="n">module</span>
<a name="cl-49"></a>    <span class="k">for</span> <span class="n">option</span> <span class="ow">in</span> <span class="n">OPTIONS</span><span class="p">:</span>
<a name="cl-50"></a>        <span class="n">directive</span> <span class="o">+=</span> <span class="s">&#39;    :</span><span class="si">%s</span><span class="s">:</span><span class="se">\n</span><span class="s">&#39;</span> <span class="o">%</span> <span class="n">option</span>
<a name="cl-51"></a>    <span class="k">return</span> <span class="n">directive</span>
<a name="cl-52"></a>
<a name="cl-53"></a><span class="k">def</span> <span class="nf">write_heading</span><span class="p">(</span><span class="n">module</span><span class="p">,</span> <span class="n">kind</span><span class="o">=</span><span class="s">&#39;Module&#39;</span><span class="p">):</span>
<a name="cl-54"></a>    <span class="sd">&quot;&quot;&quot;Create the page heading.&quot;&quot;&quot;</span>
<a name="cl-55"></a>    <span class="n">module</span> <span class="o">=</span> <span class="n">module</span><span class="o">.</span><span class="n">title</span><span class="p">()</span>
<a name="cl-56"></a>    <span class="n">heading</span> <span class="o">=</span> <span class="n">title_line</span><span class="p">(</span><span class="n">module</span> <span class="o">+</span> <span class="s">&#39; Documentation&#39;</span><span class="p">,</span> <span class="s">&#39;=&#39;</span><span class="p">)</span>
<a name="cl-57"></a>    <span class="n">heading</span> <span class="o">+=</span> <span class="s">&#39;This page contains the </span><span class="si">%s</span><span class="s"> </span><span class="si">%s</span><span class="s"> documentation.</span><span class="se">\n\n</span><span class="s">&#39;</span> <span class="o">%</span> <span class="p">(</span><span class="n">module</span><span class="p">,</span> <span class="n">kind</span><span class="p">)</span>
<a name="cl-58"></a>    <span class="k">return</span> <span class="n">heading</span>
<a name="cl-59"></a>
<a name="cl-60"></a><span class="k">def</span> <span class="nf">write_sub</span><span class="p">(</span><span class="n">module</span><span class="p">,</span> <span class="n">kind</span><span class="o">=</span><span class="s">&#39;Module&#39;</span><span class="p">):</span>
<a name="cl-61"></a>    <span class="sd">&quot;&quot;&quot;Create the module subtitle&quot;&quot;&quot;</span>
<a name="cl-62"></a>    <span class="n">sub</span> <span class="o">=</span> <span class="n">title_line</span><span class="p">(</span><span class="s">&#39;The :mod:`</span><span class="si">%s</span><span class="s">` </span><span class="si">%s</span><span class="s">&#39;</span> <span class="o">%</span> <span class="p">(</span><span class="n">module</span><span class="p">,</span> <span class="n">kind</span><span class="p">),</span> <span class="s">&#39;-&#39;</span><span class="p">)</span>
<a name="cl-63"></a>    <span class="k">return</span> <span class="n">sub</span>
<a name="cl-64"></a>
<a name="cl-65"></a><span class="k">def</span> <span class="nf">title_line</span><span class="p">(</span><span class="n">title</span><span class="p">,</span> <span class="n">char</span><span class="p">):</span>
<a name="cl-66"></a>    <span class="sd">&quot;&quot;&quot; Underline the title with the character pass, with the right length.&quot;&quot;&quot;</span>
<a name="cl-67"></a>    <span class="k">return</span> <span class="s">&#39;</span><span class="si">%s</span><span class="se">\n</span><span class="si">%s</span><span class="se">\n\n</span><span class="s">&#39;</span> <span class="o">%</span> <span class="p">(</span><span class="n">title</span><span class="p">,</span> <span class="nb">len</span><span class="p">(</span><span class="n">title</span><span class="p">)</span> <span class="o">*</span> <span class="n">char</span><span class="p">)</span>
<a name="cl-68"></a>
<a name="cl-69"></a><span class="k">def</span> <span class="nf">create_module_file</span><span class="p">(</span><span class="n">package</span><span class="p">,</span> <span class="n">module</span><span class="p">,</span> <span class="n">opts</span><span class="p">):</span>
<a name="cl-70"></a>    <span class="sd">&quot;&quot;&quot;Build the text of the file and write the file.&quot;&quot;&quot;</span>
<a name="cl-71"></a>    <span class="n">name</span> <span class="o">=</span> <span class="n">create_file_name</span><span class="p">(</span><span class="n">module</span><span class="p">,</span> <span class="n">opts</span><span class="p">)</span>
<a name="cl-72"></a>    <span class="k">if</span> <span class="ow">not</span> <span class="n">opts</span><span class="o">.</span><span class="n">force</span> <span class="ow">and</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">isfile</span><span class="p">(</span><span class="n">name</span><span class="p">):</span>
<a name="cl-73"></a>        <span class="k">print</span> <span class="s">&#39;File </span><span class="si">%s</span><span class="s"> already exists.&#39;</span> <span class="o">%</span> <span class="n">name</span>
<a name="cl-74"></a>    <span class="k">else</span><span class="p">:</span>
<a name="cl-75"></a>        <span class="k">print</span> <span class="s">&#39;Creating file </span><span class="si">%s</span><span class="s"> (module).&#39;</span> <span class="o">%</span> <span class="n">name</span>
<a name="cl-76"></a>        <span class="n">text</span> <span class="o">=</span> <span class="n">write_heading</span><span class="p">(</span><span class="n">module</span><span class="p">)</span>
<a name="cl-77"></a>        <span class="n">text</span> <span class="o">+=</span> <span class="n">write_sub</span><span class="p">(</span><span class="n">module</span><span class="p">)</span>
<a name="cl-78"></a>        <span class="n">text</span> <span class="o">+=</span> <span class="n">write_directive</span><span class="p">(</span><span class="n">module</span><span class="p">,</span> <span class="n">package</span><span class="p">)</span>
<a name="cl-79"></a>
<a name="cl-80"></a>        <span class="c"># write the file</span>
<a name="cl-81"></a>        <span class="k">if</span> <span class="ow">not</span> <span class="n">opts</span><span class="o">.</span><span class="n">dryrun</span><span class="p">:</span>       
<a name="cl-82"></a>            <span class="n">fd</span> <span class="o">=</span> <span class="nb">open</span><span class="p">(</span><span class="n">name</span><span class="p">,</span> <span class="s">&#39;w&#39;</span><span class="p">)</span>
<a name="cl-83"></a>            <span class="n">fd</span><span class="o">.</span><span class="n">write</span><span class="p">(</span><span class="n">text</span><span class="p">)</span>
<a name="cl-84"></a>            <span class="n">fd</span><span class="o">.</span><span class="n">close</span><span class="p">()</span>
<a name="cl-85"></a>
<a name="cl-86"></a><span class="k">def</span> <span class="nf">create_package_file</span><span class="p">(</span><span class="n">root</span><span class="p">,</span> <span class="n">master_package</span><span class="p">,</span> <span class="n">subroot</span><span class="p">,</span> <span class="n">py_files</span><span class="p">,</span> <span class="n">opts</span><span class="p">,</span> <span class="n">subs</span><span class="o">=</span><span class="bp">None</span><span class="p">):</span>
<a name="cl-87"></a>    <span class="sd">&quot;&quot;&quot;Build the text of the file and write the file.&quot;&quot;&quot;</span>
<a name="cl-88"></a>    <span class="n">package</span> <span class="o">=</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">split</span><span class="p">(</span><span class="n">root</span><span class="p">)[</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span><span class="o">.</span><span class="n">lower</span><span class="p">()</span>
<a name="cl-89"></a>    <span class="n">name</span> <span class="o">=</span> <span class="n">create_file_name</span><span class="p">(</span><span class="n">subroot</span><span class="p">,</span> <span class="n">opts</span><span class="p">)</span>
<a name="cl-90"></a>    <span class="k">if</span> <span class="ow">not</span> <span class="n">opts</span><span class="o">.</span><span class="n">force</span> <span class="ow">and</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">isfile</span><span class="p">(</span><span class="n">name</span><span class="p">):</span>
<a name="cl-91"></a>        <span class="k">print</span> <span class="s">&#39;File </span><span class="si">%s</span><span class="s"> already exists.&#39;</span> <span class="o">%</span> <span class="n">name</span>
<a name="cl-92"></a>    <span class="k">else</span><span class="p">:</span>
<a name="cl-93"></a>        <span class="k">print</span> <span class="s">&#39;Creating file </span><span class="si">%s</span><span class="s"> (package).&#39;</span> <span class="o">%</span> <span class="n">name</span>
<a name="cl-94"></a>        <span class="n">text</span> <span class="o">=</span> <span class="n">write_heading</span><span class="p">(</span><span class="n">package</span><span class="p">,</span> <span class="s">&#39;Package&#39;</span><span class="p">)</span>
<a name="cl-95"></a>        <span class="k">if</span> <span class="n">subs</span> <span class="o">==</span> <span class="bp">None</span><span class="p">:</span>
<a name="cl-96"></a>            <span class="n">subs</span> <span class="o">=</span> <span class="p">[]</span>
<a name="cl-97"></a>        <span class="k">else</span><span class="p">:</span>
<a name="cl-98"></a>            <span class="c"># build a list of directories that are package (they contain an __init_.py file)</span>
<a name="cl-99"></a>            <span class="n">subs</span> <span class="o">=</span> <span class="p">[</span><span class="n">sub</span> <span class="k">for</span> <span class="n">sub</span> <span class="ow">in</span> <span class="n">subs</span> <span class="k">if</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">isfile</span><span class="p">(</span><span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">join</span><span class="p">(</span><span class="n">root</span><span class="p">,</span> <span class="n">sub</span><span class="p">,</span> <span class="s">&#39;__init__.py&#39;</span><span class="p">))]</span>
<a name="cl-100"></a>            <span class="c"># if there&#39;s some package directories, add a TOC for theses subpackages</span>
<a name="cl-101"></a>            <span class="k">if</span> <span class="n">subs</span><span class="p">:</span>
<a name="cl-102"></a>                <span class="n">text</span> <span class="o">+=</span> <span class="n">title_line</span><span class="p">(</span><span class="s">&#39;Subpackages&#39;</span><span class="p">,</span> <span class="s">&#39;-&#39;</span><span class="p">)</span>
<a name="cl-103"></a>                <span class="n">text</span> <span class="o">+=</span> <span class="s">&#39;.. toctree::</span><span class="se">\n\n</span><span class="s">&#39;</span>
<a name="cl-104"></a>                <span class="k">for</span> <span class="n">sub</span> <span class="ow">in</span> <span class="n">subs</span><span class="p">:</span>
<a name="cl-105"></a>                    <span class="n">text</span> <span class="o">+=</span> <span class="s">&#39;    </span><span class="si">%s</span><span class="s">.</span><span class="si">%s</span><span class="se">\n</span><span class="s">&#39;</span> <span class="o">%</span> <span class="p">(</span><span class="n">subroot</span><span class="p">,</span> <span class="n">sub</span><span class="p">)</span>
<a name="cl-106"></a>                <span class="n">text</span> <span class="o">+=</span> <span class="s">&#39;</span><span class="se">\n</span><span class="s">&#39;</span>
<a name="cl-107"></a>                    
<a name="cl-108"></a>        <span class="c"># add each package&#39;s module</span>
<a name="cl-109"></a>        <span class="k">for</span> <span class="n">py_file</span> <span class="ow">in</span> <span class="n">py_files</span><span class="p">:</span>
<a name="cl-110"></a>            <span class="k">if</span> <span class="ow">not</span> <span class="n">check_for_code</span><span class="p">(</span><span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">join</span><span class="p">(</span><span class="n">root</span><span class="p">,</span> <span class="n">py_file</span><span class="p">)):</span>
<a name="cl-111"></a>                <span class="c"># don&#39;t build the file if there&#39;s no code in it</span>
<a name="cl-112"></a>                <span class="k">continue</span>
<a name="cl-113"></a>            <span class="n">py_file</span> <span class="o">=</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">splitext</span><span class="p">(</span><span class="n">py_file</span><span class="p">)[</span><span class="mi">0</span><span class="p">]</span>
<a name="cl-114"></a>            <span class="n">py_path</span> <span class="o">=</span> <span class="s">&#39;</span><span class="si">%s</span><span class="s">.</span><span class="si">%s</span><span class="s">&#39;</span> <span class="o">%</span> <span class="p">(</span><span class="n">subroot</span><span class="p">,</span> <span class="n">py_file</span><span class="p">)</span>
<a name="cl-115"></a>            <span class="n">kind</span> <span class="o">=</span> <span class="s">&quot;Module&quot;</span>
<a name="cl-116"></a>            <span class="k">if</span> <span class="n">py_file</span> <span class="o">==</span> <span class="s">&#39;__init__&#39;</span><span class="p">:</span>
<a name="cl-117"></a>                <span class="n">kind</span> <span class="o">=</span> <span class="s">&quot;Package&quot;</span>
<a name="cl-118"></a>            <span class="n">text</span> <span class="o">+=</span> <span class="n">write_sub</span><span class="p">(</span><span class="n">kind</span> <span class="o">==</span> <span class="s">&#39;Package&#39;</span> <span class="ow">and</span> <span class="n">package</span> <span class="ow">or</span> <span class="n">py_file</span><span class="p">,</span> <span class="n">kind</span><span class="p">)</span>
<a name="cl-119"></a>            <span class="n">text</span> <span class="o">+=</span> <span class="n">write_directive</span><span class="p">(</span><span class="n">kind</span> <span class="o">==</span> <span class="s">&quot;Package&quot;</span> <span class="ow">and</span> <span class="n">subroot</span> <span class="ow">or</span> <span class="n">py_path</span><span class="p">,</span> <span class="n">master_package</span><span class="p">)</span>
<a name="cl-120"></a>            <span class="n">text</span> <span class="o">+=</span> <span class="s">&#39;</span><span class="se">\n</span><span class="s">&#39;</span>
<a name="cl-121"></a>
<a name="cl-122"></a>        <span class="c"># write the file</span>
<a name="cl-123"></a>        <span class="k">if</span> <span class="ow">not</span> <span class="n">opts</span><span class="o">.</span><span class="n">dryrun</span><span class="p">:</span>       
<a name="cl-124"></a>            <span class="n">fd</span> <span class="o">=</span> <span class="nb">open</span><span class="p">(</span><span class="n">name</span><span class="p">,</span> <span class="s">&#39;w&#39;</span><span class="p">)</span>
<a name="cl-125"></a>            <span class="n">fd</span><span class="o">.</span><span class="n">write</span><span class="p">(</span><span class="n">text</span><span class="p">)</span>
<a name="cl-126"></a>            <span class="n">fd</span><span class="o">.</span><span class="n">close</span><span class="p">()</span>
<a name="cl-127"></a>
<a name="cl-128"></a><span class="k">def</span> <span class="nf">check_for_code</span><span class="p">(</span><span class="n">module</span><span class="p">):</span>
<a name="cl-129"></a>    <span class="sd">&quot;&quot;&quot;</span>
<a name="cl-130"></a><span class="sd">    Check if there&#39;s at least one class or one function in the module.</span>
<a name="cl-131"></a><span class="sd">    &quot;&quot;&quot;</span>
<a name="cl-132"></a>    <span class="n">fd</span> <span class="o">=</span> <span class="nb">open</span><span class="p">(</span><span class="n">module</span><span class="p">,</span> <span class="s">&#39;r&#39;</span><span class="p">)</span>
<a name="cl-133"></a>    <span class="k">for</span> <span class="n">line</span> <span class="ow">in</span> <span class="n">fd</span><span class="p">:</span>
<a name="cl-134"></a>        <span class="k">if</span> <span class="n">line</span><span class="o">.</span><span class="n">startswith</span><span class="p">(</span><span class="s">&#39;def &#39;</span><span class="p">)</span> <span class="ow">or</span> <span class="n">line</span><span class="o">.</span><span class="n">startswith</span><span class="p">(</span><span class="s">&#39;class &#39;</span><span class="p">):</span>
<a name="cl-135"></a>            <span class="n">fd</span><span class="o">.</span><span class="n">close</span><span class="p">()</span>
<a name="cl-136"></a>            <span class="k">return</span> <span class="bp">True</span>
<a name="cl-137"></a>    <span class="n">fd</span><span class="o">.</span><span class="n">close</span><span class="p">()</span>
<a name="cl-138"></a>    <span class="k">return</span> <span class="bp">False</span>
<a name="cl-139"></a>        
<a name="cl-140"></a><span class="k">def</span> <span class="nf">recurse_tree</span><span class="p">(</span><span class="n">path</span><span class="p">,</span> <span class="n">excludes</span><span class="p">,</span> <span class="n">opts</span><span class="p">):</span>
<a name="cl-141"></a>    <span class="sd">&quot;&quot;&quot;</span>
<a name="cl-142"></a><span class="sd">    Look for every file in the directory tree and create the corresponding</span>
<a name="cl-143"></a><span class="sd">    ReST files.</span>
<a name="cl-144"></a><span class="sd">    &quot;&quot;&quot;</span>
<a name="cl-145"></a>    <span class="n">package_name</span> <span class="o">=</span> <span class="bp">None</span>
<a name="cl-146"></a>    <span class="c"># check if the base directory is a package and get is name</span>
<a name="cl-147"></a>    <span class="k">if</span> <span class="s">&#39;__init__.py&#39;</span> <span class="ow">in</span> <span class="n">os</span><span class="o">.</span><span class="n">listdir</span><span class="p">(</span><span class="n">path</span><span class="p">):</span>
<a name="cl-148"></a>        <span class="n">package_name</span> <span class="o">=</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">abspath</span><span class="p">(</span><span class="n">path</span><span class="p">)</span><span class="o">.</span><span class="n">split</span><span class="p">(</span><span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">sep</span><span class="p">)[</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span>
<a name="cl-149"></a>    
<a name="cl-150"></a>    <span class="n">toc</span> <span class="o">=</span> <span class="p">[]</span>
<a name="cl-151"></a>    <span class="n">excludes</span> <span class="o">=</span> <span class="n">format_excludes</span><span class="p">(</span><span class="n">path</span><span class="p">,</span> <span class="n">excludes</span><span class="p">)</span>
<a name="cl-152"></a>    <span class="n">tree</span> <span class="o">=</span> <span class="n">os</span><span class="o">.</span><span class="n">walk</span><span class="p">(</span><span class="n">path</span><span class="p">,</span> <span class="bp">False</span><span class="p">)</span>
<a name="cl-153"></a>    <span class="k">for</span> <span class="n">root</span><span class="p">,</span> <span class="n">subs</span><span class="p">,</span> <span class="n">files</span> <span class="ow">in</span> <span class="n">tree</span><span class="p">:</span>
<a name="cl-154"></a>        <span class="c"># keep only the Python script files</span>
<a name="cl-155"></a>        <span class="n">py_files</span> <span class="o">=</span> <span class="n">check_py_file</span><span class="p">(</span><span class="n">files</span><span class="p">)</span>
<a name="cl-156"></a>        <span class="c"># remove hidden (&#39;.&#39;) and private (&#39;_&#39;) directories</span>
<a name="cl-157"></a>        <span class="n">subs</span> <span class="o">=</span> <span class="p">[</span><span class="n">sub</span> <span class="k">for</span> <span class="n">sub</span> <span class="ow">in</span> <span class="n">subs</span> <span class="k">if</span> <span class="n">sub</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span> <span class="ow">not</span> <span class="ow">in</span> <span class="p">[</span><span class="s">&#39;.&#39;</span><span class="p">,</span> <span class="s">&#39;_&#39;</span><span class="p">]]</span>
<a name="cl-158"></a>        <span class="c"># check if there&#39;s valid files to process</span>
<a name="cl-159"></a>        <span class="c"># TODO: could add check for windows hidden files</span>
<a name="cl-160"></a>        <span class="k">if</span> <span class="s">&quot;/.&quot;</span> <span class="ow">in</span> <span class="n">root</span> <span class="ow">or</span> <span class="s">&quot;/_&quot;</span> <span class="ow">in</span> <span class="n">root</span> \
<a name="cl-161"></a>        <span class="ow">or</span> <span class="ow">not</span> <span class="n">py_files</span> \
<a name="cl-162"></a>        <span class="ow">or</span> <span class="n">check_excludes</span><span class="p">(</span><span class="n">root</span><span class="p">,</span> <span class="n">excludes</span><span class="p">):</span>
<a name="cl-163"></a>            <span class="k">continue</span>
<a name="cl-164"></a>        <span class="n">subroot</span> <span class="o">=</span> <span class="n">root</span><span class="p">[</span><span class="nb">len</span><span class="p">(</span><span class="n">path</span><span class="p">):]</span><span class="o">.</span><span class="n">lstrip</span><span class="p">(</span><span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">sep</span><span class="p">)</span><span class="o">.</span><span class="n">replace</span><span class="p">(</span><span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">sep</span><span class="p">,</span> <span class="s">&#39;.&#39;</span><span class="p">)</span>
<a name="cl-165"></a>        <span class="k">if</span> <span class="n">root</span> <span class="o">==</span> <span class="n">path</span><span class="p">:</span>
<a name="cl-166"></a>            <span class="c"># we are at the root level so we create only modules</span>
<a name="cl-167"></a>            <span class="k">for</span> <span class="n">py_file</span> <span class="ow">in</span> <span class="n">py_files</span><span class="p">:</span>
<a name="cl-168"></a>                <span class="n">module</span> <span class="o">=</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">splitext</span><span class="p">(</span><span class="n">py_file</span><span class="p">)[</span><span class="mi">0</span><span class="p">]</span>
<a name="cl-169"></a>                <span class="c"># add the module if it contains code</span>
<a name="cl-170"></a>                <span class="k">if</span> <span class="n">check_for_code</span><span class="p">(</span><span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">join</span><span class="p">(</span><span class="n">path</span><span class="p">,</span> <span class="s">&#39;</span><span class="si">%s</span><span class="s">.py&#39;</span> <span class="o">%</span> <span class="n">module</span><span class="p">)):</span>
<a name="cl-171"></a>                    <span class="n">create_module_file</span><span class="p">(</span><span class="n">package_name</span><span class="p">,</span> <span class="n">module</span><span class="p">,</span> <span class="n">opts</span><span class="p">)</span>
<a name="cl-172"></a>                    <span class="n">toc</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="n">module</span><span class="p">)</span>
<a name="cl-173"></a>        <span class="k">elif</span> <span class="ow">not</span> <span class="n">subs</span> <span class="ow">and</span> <span class="s">&quot;__init__.py&quot;</span> <span class="ow">in</span> <span class="n">py_files</span><span class="p">:</span>
<a name="cl-174"></a>            <span class="c"># we are in a package without sub package</span>
<a name="cl-175"></a>            <span class="c"># check if there&#39;s only an __init__.py file</span>
<a name="cl-176"></a>            <span class="k">if</span> <span class="nb">len</span><span class="p">(</span><span class="n">py_files</span><span class="p">)</span> <span class="o">==</span> <span class="mi">1</span><span class="p">:</span>
<a name="cl-177"></a>                <span class="c"># check if there&#39;s code in the __init__.py file</span>
<a name="cl-178"></a>                <span class="k">if</span> <span class="n">check_for_code</span><span class="p">(</span><span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">join</span><span class="p">(</span><span class="n">root</span><span class="p">,</span> <span class="s">&#39;__init__.py&#39;</span><span class="p">)):</span>
<a name="cl-179"></a>                    <span class="n">create_package_file</span><span class="p">(</span><span class="n">root</span><span class="p">,</span> <span class="n">package_name</span><span class="p">,</span> <span class="n">subroot</span><span class="p">,</span> <span class="n">py_files</span><span class="p">,</span> <span class="n">opts</span><span class="o">=</span><span class="n">opts</span><span class="p">)</span>
<a name="cl-180"></a>                    <span class="n">toc</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="n">subroot</span><span class="p">)</span>
<a name="cl-181"></a>            <span class="k">else</span><span class="p">:</span>
<a name="cl-182"></a>                <span class="n">create_package_file</span><span class="p">(</span><span class="n">root</span><span class="p">,</span> <span class="n">package_name</span><span class="p">,</span> <span class="n">subroot</span><span class="p">,</span> <span class="n">py_files</span><span class="p">,</span> <span class="n">opts</span><span class="o">=</span><span class="n">opts</span><span class="p">)</span>
<a name="cl-183"></a>                <span class="n">toc</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="n">subroot</span><span class="p">)</span>
<a name="cl-184"></a>        <span class="k">elif</span> <span class="s">&quot;__init__.py&quot;</span> <span class="ow">in</span> <span class="n">py_files</span><span class="p">:</span>
<a name="cl-185"></a>            <span class="c"># we are in package with subpackage(s)</span>
<a name="cl-186"></a>            <span class="n">create_package_file</span><span class="p">(</span><span class="n">root</span><span class="p">,</span> <span class="n">package_name</span><span class="p">,</span> <span class="n">subroot</span><span class="p">,</span> <span class="n">py_files</span><span class="p">,</span> <span class="n">opts</span><span class="p">,</span> <span class="n">subs</span><span class="p">)</span>
<a name="cl-187"></a>            <span class="n">toc</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="n">subroot</span><span class="p">)</span>
<a name="cl-188"></a>            
<a name="cl-189"></a>    <span class="c"># create the module&#39;s index</span>
<a name="cl-190"></a>    <span class="k">if</span> <span class="ow">not</span> <span class="n">opts</span><span class="o">.</span><span class="n">notoc</span><span class="p">:</span>
<a name="cl-191"></a>        <span class="n">modules_toc</span><span class="p">(</span><span class="n">toc</span><span class="p">,</span> <span class="n">opts</span><span class="p">)</span>
<a name="cl-192"></a>
<a name="cl-193"></a><span class="k">def</span> <span class="nf">modules_toc</span><span class="p">(</span><span class="n">modules</span><span class="p">,</span> <span class="n">opts</span><span class="p">,</span> <span class="n">name</span><span class="o">=</span><span class="s">&#39;modules&#39;</span><span class="p">):</span>
<a name="cl-194"></a>    <span class="sd">&quot;&quot;&quot;</span>
<a name="cl-195"></a><span class="sd">    Create the module&#39;s index.</span>
<a name="cl-196"></a><span class="sd">    &quot;&quot;&quot;</span>
<a name="cl-197"></a>    <span class="n">fname</span> <span class="o">=</span> <span class="n">create_file_name</span><span class="p">(</span><span class="n">name</span><span class="p">,</span> <span class="n">opts</span><span class="p">)</span>    
<a name="cl-198"></a>    <span class="k">if</span> <span class="ow">not</span> <span class="n">opts</span><span class="o">.</span><span class="n">force</span> <span class="ow">and</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">exists</span><span class="p">(</span><span class="n">fname</span><span class="p">):</span>
<a name="cl-199"></a>        <span class="k">print</span> <span class="s">&quot;File </span><span class="si">%s</span><span class="s"> already exists.&quot;</span> <span class="o">%</span> <span class="n">name</span>
<a name="cl-200"></a>        <span class="k">return</span>
<a name="cl-201"></a>
<a name="cl-202"></a>    <span class="k">print</span> <span class="s">&quot;Creating module&#39;s index modules.txt.&quot;</span>
<a name="cl-203"></a>    <span class="n">text</span> <span class="o">=</span> <span class="n">write_heading</span><span class="p">(</span><span class="n">opts</span><span class="o">.</span><span class="n">header</span><span class="p">,</span> <span class="s">&#39;Modules&#39;</span><span class="p">)</span>
<a name="cl-204"></a>    <span class="n">text</span> <span class="o">+=</span> <span class="n">title_line</span><span class="p">(</span><span class="s">&#39;Modules:&#39;</span><span class="p">,</span> <span class="s">&#39;-&#39;</span><span class="p">)</span>
<a name="cl-205"></a>    <span class="n">text</span> <span class="o">+=</span> <span class="s">&#39;.. toctree::</span><span class="se">\n</span><span class="s">&#39;</span>
<a name="cl-206"></a>    <span class="n">text</span> <span class="o">+=</span> <span class="s">&#39;   :maxdepth: </span><span class="si">%s</span><span class="se">\n\n</span><span class="s">&#39;</span> <span class="o">%</span> <span class="n">opts</span><span class="o">.</span><span class="n">maxdepth</span>
<a name="cl-207"></a>    
<a name="cl-208"></a>    <span class="n">modules</span><span class="o">.</span><span class="n">sort</span><span class="p">()</span>
<a name="cl-209"></a>    <span class="n">prev_module</span> <span class="o">=</span> <span class="s">&#39;&#39;</span>
<a name="cl-210"></a>    <span class="k">for</span> <span class="n">module</span> <span class="ow">in</span> <span class="n">modules</span><span class="p">:</span>
<a name="cl-211"></a>        <span class="c"># look if the module is a subpackage and, if yes, ignore it</span>
<a name="cl-212"></a>        <span class="k">if</span> <span class="n">module</span><span class="o">.</span><span class="n">startswith</span><span class="p">(</span><span class="n">prev_module</span> <span class="o">+</span> <span class="s">&#39;.&#39;</span><span class="p">):</span>
<a name="cl-213"></a>            <span class="k">continue</span>
<a name="cl-214"></a>        <span class="n">prev_module</span> <span class="o">=</span> <span class="n">module</span>
<a name="cl-215"></a>        <span class="n">text</span> <span class="o">+=</span> <span class="s">&#39;   </span><span class="si">%s</span><span class="se">\n</span><span class="s">&#39;</span> <span class="o">%</span> <span class="n">module</span>
<a name="cl-216"></a>        
<a name="cl-217"></a>    <span class="c"># write the file</span>
<a name="cl-218"></a>    <span class="k">if</span> <span class="ow">not</span> <span class="n">opts</span><span class="o">.</span><span class="n">dryrun</span><span class="p">:</span>       
<a name="cl-219"></a>        <span class="n">fd</span> <span class="o">=</span> <span class="nb">open</span><span class="p">(</span><span class="n">fname</span><span class="p">,</span> <span class="s">&#39;w&#39;</span><span class="p">)</span>
<a name="cl-220"></a>        <span class="n">fd</span><span class="o">.</span><span class="n">write</span><span class="p">(</span><span class="n">text</span><span class="p">)</span>
<a name="cl-221"></a>        <span class="n">fd</span><span class="o">.</span><span class="n">close</span><span class="p">()</span>
<a name="cl-222"></a>
<a name="cl-223"></a><span class="k">def</span> <span class="nf">format_excludes</span><span class="p">(</span><span class="n">path</span><span class="p">,</span> <span class="n">excludes</span><span class="p">):</span>
<a name="cl-224"></a>    <span class="sd">&quot;&quot;&quot;</span>
<a name="cl-225"></a><span class="sd">    Format the excluded directory list.</span>
<a name="cl-226"></a><span class="sd">    (verify that the path is not from the root of the volume or the root of the</span>
<a name="cl-227"></a><span class="sd">    package)</span>
<a name="cl-228"></a><span class="sd">    &quot;&quot;&quot;</span>
<a name="cl-229"></a>    <span class="n">f_excludes</span> <span class="o">=</span> <span class="p">[]</span>
<a name="cl-230"></a>    <span class="k">for</span> <span class="n">exclude</span> <span class="ow">in</span> <span class="n">excludes</span><span class="p">:</span>
<a name="cl-231"></a>        <span class="k">if</span> <span class="ow">not</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">isabs</span><span class="p">(</span><span class="n">exclude</span><span class="p">)</span> <span class="ow">and</span> <span class="n">exclude</span><span class="p">[:</span><span class="nb">len</span><span class="p">(</span><span class="n">path</span><span class="p">)]</span> <span class="o">!=</span> <span class="n">path</span><span class="p">:</span>
<a name="cl-232"></a>            <span class="n">exclude</span> <span class="o">=</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">join</span><span class="p">(</span><span class="n">path</span><span class="p">,</span> <span class="n">exclude</span><span class="p">)</span>
<a name="cl-233"></a>        <span class="c"># remove trailing slash</span>
<a name="cl-234"></a>        <span class="n">f_excludes</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="n">exclude</span><span class="o">.</span><span class="n">rstrip</span><span class="p">(</span><span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">sep</span><span class="p">))</span>
<a name="cl-235"></a>    <span class="k">return</span> <span class="n">f_excludes</span>
<a name="cl-236"></a>
<a name="cl-237"></a><span class="k">def</span> <span class="nf">check_excludes</span><span class="p">(</span><span class="n">root</span><span class="p">,</span> <span class="n">excludes</span><span class="p">):</span>
<a name="cl-238"></a>    <span class="sd">&quot;&quot;&quot;</span>
<a name="cl-239"></a><span class="sd">    Check if the directory is in the exclude list.</span>
<a name="cl-240"></a><span class="sd">    &quot;&quot;&quot;</span>
<a name="cl-241"></a>    <span class="k">for</span> <span class="n">exclude</span> <span class="ow">in</span> <span class="n">excludes</span><span class="p">:</span>
<a name="cl-242"></a>        <span class="k">if</span> <span class="n">root</span><span class="p">[:</span><span class="nb">len</span><span class="p">(</span><span class="n">exclude</span><span class="p">)]</span> <span class="o">==</span> <span class="n">exclude</span><span class="p">:</span>
<a name="cl-243"></a>            <span class="k">return</span> <span class="bp">True</span>
<a name="cl-244"></a>    <span class="k">return</span> <span class="bp">False</span>
<a name="cl-245"></a>
<a name="cl-246"></a><span class="k">def</span> <span class="nf">check_py_file</span><span class="p">(</span><span class="n">files</span><span class="p">):</span>
<a name="cl-247"></a>    <span class="sd">&quot;&quot;&quot;</span>
<a name="cl-248"></a><span class="sd">    Return a list with only the python scripts (remove all other files). </span>
<a name="cl-249"></a><span class="sd">    &quot;&quot;&quot;</span>
<a name="cl-250"></a>    <span class="n">py_files</span> <span class="o">=</span> <span class="p">[</span><span class="n">fich</span> <span class="k">for</span> <span class="n">fich</span> <span class="ow">in</span> <span class="n">files</span> <span class="k">if</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">splitext</span><span class="p">(</span><span class="n">fich</span><span class="p">)[</span><span class="mi">1</span><span class="p">]</span> <span class="o">==</span> <span class="s">&#39;.py&#39;</span><span class="p">]</span>
<a name="cl-251"></a>    <span class="k">return</span> <span class="n">py_files</span>
<a name="cl-252"></a>
<a name="cl-253"></a>
<a name="cl-254"></a><span class="k">def</span> <span class="nf">main</span><span class="p">():</span>
<a name="cl-255"></a>    <span class="sd">&quot;&quot;&quot;</span>
<a name="cl-256"></a><span class="sd">    Parse and check the command line arguments</span>
<a name="cl-257"></a><span class="sd">    &quot;&quot;&quot;</span>
<a name="cl-258"></a>    <span class="n">parser</span> <span class="o">=</span> <span class="n">optparse</span><span class="o">.</span><span class="n">OptionParser</span><span class="p">(</span><span class="n">usage</span><span class="o">=</span><span class="s">&quot;&quot;&quot;usage: %prog [options] &lt;package path&gt; [exclude paths, ...]</span>
<a name="cl-259"></a><span class="s">    </span>
<a name="cl-260"></a><span class="s">Note: By default this script will not overwrite already created files.&quot;&quot;&quot;</span><span class="p">)</span>
<a name="cl-261"></a>    <span class="n">parser</span><span class="o">.</span><span class="n">add_option</span><span class="p">(</span><span class="s">&quot;-n&quot;</span><span class="p">,</span> <span class="s">&quot;--doc-header&quot;</span><span class="p">,</span> <span class="n">action</span><span class="o">=</span><span class="s">&quot;store&quot;</span><span class="p">,</span> <span class="n">dest</span><span class="o">=</span><span class="s">&quot;header&quot;</span><span class="p">,</span> <span class="n">help</span><span class="o">=</span><span class="s">&quot;Documentation Header (default=Project)&quot;</span><span class="p">,</span> <span class="n">default</span><span class="o">=</span><span class="s">&quot;Project&quot;</span><span class="p">)</span>
<a name="cl-262"></a>    <span class="n">parser</span><span class="o">.</span><span class="n">add_option</span><span class="p">(</span><span class="s">&quot;-d&quot;</span><span class="p">,</span> <span class="s">&quot;--dest-dir&quot;</span><span class="p">,</span> <span class="n">action</span><span class="o">=</span><span class="s">&quot;store&quot;</span><span class="p">,</span> <span class="n">dest</span><span class="o">=</span><span class="s">&quot;destdir&quot;</span><span class="p">,</span> <span class="n">help</span><span class="o">=</span><span class="s">&quot;Output destination directory&quot;</span><span class="p">,</span> <span class="n">default</span><span class="o">=</span><span class="s">&quot;&quot;</span><span class="p">)</span>
<a name="cl-263"></a>    <span class="n">parser</span><span class="o">.</span><span class="n">add_option</span><span class="p">(</span><span class="s">&quot;-s&quot;</span><span class="p">,</span> <span class="s">&quot;--suffix&quot;</span><span class="p">,</span> <span class="n">action</span><span class="o">=</span><span class="s">&quot;store&quot;</span><span class="p">,</span> <span class="n">dest</span><span class="o">=</span><span class="s">&quot;suffix&quot;</span><span class="p">,</span> <span class="n">help</span><span class="o">=</span><span class="s">&quot;module suffix (default=txt)&quot;</span><span class="p">,</span> <span class="n">default</span><span class="o">=</span><span class="s">&quot;txt&quot;</span><span class="p">)</span>
<a name="cl-264"></a>    <span class="n">parser</span><span class="o">.</span><span class="n">add_option</span><span class="p">(</span><span class="s">&quot;-m&quot;</span><span class="p">,</span> <span class="s">&quot;--maxdepth&quot;</span><span class="p">,</span> <span class="n">action</span><span class="o">=</span><span class="s">&quot;store&quot;</span><span class="p">,</span> <span class="n">dest</span><span class="o">=</span><span class="s">&quot;maxdepth&quot;</span><span class="p">,</span> <span class="n">help</span><span class="o">=</span><span class="s">&quot;Maximum depth of submodules to show in the TOC (default=4)&quot;</span><span class="p">,</span> <span class="nb">type</span><span class="o">=</span><span class="s">&quot;int&quot;</span><span class="p">,</span> <span class="n">default</span><span class="o">=</span><span class="mi">4</span><span class="p">)</span>
<a name="cl-265"></a>    <span class="n">parser</span><span class="o">.</span><span class="n">add_option</span><span class="p">(</span><span class="s">&quot;-r&quot;</span><span class="p">,</span> <span class="s">&quot;--dry-run&quot;</span><span class="p">,</span> <span class="n">action</span><span class="o">=</span><span class="s">&quot;store_true&quot;</span><span class="p">,</span> <span class="n">dest</span><span class="o">=</span><span class="s">&quot;dryrun&quot;</span><span class="p">,</span> <span class="n">help</span><span class="o">=</span><span class="s">&quot;Run the script without creating the files&quot;</span><span class="p">)</span>
<a name="cl-266"></a>    <span class="n">parser</span><span class="o">.</span><span class="n">add_option</span><span class="p">(</span><span class="s">&quot;-f&quot;</span><span class="p">,</span> <span class="s">&quot;--force&quot;</span><span class="p">,</span> <span class="n">action</span><span class="o">=</span><span class="s">&quot;store_true&quot;</span><span class="p">,</span> <span class="n">dest</span><span class="o">=</span><span class="s">&quot;force&quot;</span><span class="p">,</span> <span class="n">help</span><span class="o">=</span><span class="s">&quot;Overwrite all the files&quot;</span><span class="p">)</span>
<a name="cl-267"></a>    <span class="n">parser</span><span class="o">.</span><span class="n">add_option</span><span class="p">(</span><span class="s">&quot;-t&quot;</span><span class="p">,</span> <span class="s">&quot;--no-toc&quot;</span><span class="p">,</span> <span class="n">action</span><span class="o">=</span><span class="s">&quot;store_true&quot;</span><span class="p">,</span> <span class="n">dest</span><span class="o">=</span><span class="s">&quot;notoc&quot;</span><span class="p">,</span> <span class="n">help</span><span class="o">=</span><span class="s">&quot;Don&#39;t create the table of content file&quot;</span><span class="p">)</span>
<a name="cl-268"></a>    <span class="p">(</span><span class="n">opts</span><span class="p">,</span> <span class="n">args</span><span class="p">)</span> <span class="o">=</span> <span class="n">parser</span><span class="o">.</span><span class="n">parse_args</span><span class="p">()</span>
<a name="cl-269"></a>    <span class="k">if</span> <span class="nb">len</span><span class="p">(</span><span class="n">args</span><span class="p">)</span> <span class="o">&lt;</span> <span class="mi">1</span><span class="p">:</span>
<a name="cl-270"></a>        <span class="n">parser</span><span class="o">.</span><span class="n">error</span><span class="p">(</span><span class="s">&quot;package path is required.&quot;</span><span class="p">)</span>
<a name="cl-271"></a>    <span class="k">else</span><span class="p">:</span>
<a name="cl-272"></a>        <span class="k">if</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">isdir</span><span class="p">(</span><span class="n">args</span><span class="p">[</span><span class="mi">0</span><span class="p">]):</span>
<a name="cl-273"></a>            <span class="c"># check if the output destination is a valid directory</span>
<a name="cl-274"></a>            <span class="k">if</span> <span class="n">opts</span><span class="o">.</span><span class="n">destdir</span> <span class="ow">and</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">isdir</span><span class="p">(</span><span class="n">opts</span><span class="o">.</span><span class="n">destdir</span><span class="p">):</span>
<a name="cl-275"></a>                <span class="c"># if there&#39;s some exclude arguments, build the list of excludes</span>
<a name="cl-276"></a>                <span class="n">excludes</span> <span class="o">=</span> <span class="n">args</span><span class="p">[</span><span class="mi">1</span><span class="p">:]</span>
<a name="cl-277"></a>                <span class="n">recurse_tree</span><span class="p">(</span><span class="n">args</span><span class="p">[</span><span class="mi">0</span><span class="p">],</span> <span class="n">excludes</span><span class="p">,</span> <span class="n">opts</span><span class="p">)</span>
<a name="cl-278"></a>            <span class="k">else</span><span class="p">:</span>
<a name="cl-279"></a>                <span class="k">print</span> <span class="s">&#39;</span><span class="si">%s</span><span class="s"> is not a valid output destination directory.&#39;</span> <span class="o">%</span> <span class="n">opts</span><span class="o">.</span><span class="n">destdir</span>
<a name="cl-280"></a>        <span class="k">else</span><span class="p">:</span>
<a name="cl-281"></a>            <span class="k">print</span> <span class="s">&#39;</span><span class="si">%s</span><span class="s"> is not a valid directory.&#39;</span> <span class="o">%</span> <span class="n">args</span>
<a name="cl-282"></a>            
<a name="cl-283"></a>            
<a name="cl-284"></a>
<a name="cl-285"></a>
<a name="cl-286"></a><span class="k">if</span> <span class="n">__name__</span> <span class="o">==</span> <span class="s">&#39;__main__&#39;</span><span class="p">:</span>
<a name="cl-287"></a>    <span class="n">main</span><span class="p">()</span>
<a name="cl-288"></a>    
</pre></div>
</td></tr></table>
		
	
</div>



			<div class="cb"></div>
		</div>
		<div class="cb footer-placeholder"></div>
	</div>
	<div id="footer-wrapper">
		<div id="footer">
			<a href="/site/terms/">TOS</a> | <a href="/site/privacy/">Privacy Policy</a> | <a href="http://blog.bitbucket.org/">Blog</a> | <a href="http://bitbucket.org/jespern/bitbucket/issues/new/">Report Bug</a> | <a href="http://groups.google.com/group/bitbucket-users">Discuss</a> | <a href="http://avantlumiere.com/">&copy; 2008-2010</a>
			| We run <small><b>
				<a href="http://www.djangoproject.com/">Django 1.2.1</a> / 
				<a href="http://bitbucket.org/jespern/django-piston/">Piston 0.2.3rc1</a> / 
				<a href="http://www.selenic.com/mercurial/">Hg 1.3.1</a> / 
				<a href="http://www.python.org">Python 2.5.2</a> /
				r3049| fe02
			</b></small>
		</div>
	</div>
	
    	<script type="text/javascript">
    	  var _gaq = _gaq || [];
    	  _gaq.push(['_setAccount', 'UA-2456069-3'], ['_trackPageview']);
    	
    	  var _gaq = _gaq || [];
    	  _gaq.push(['atl._setAccount', 'UA-6032469-33'], ['atl._trackPageview']);
    	  (function() {
    	    var ga = document.createElement('script');
    	    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 
    	        'http://www') + '.google-analytics.com/ga.js';
    	    ga.setAttribute('async', 'true');
    	    document.documentElement.firstChild.appendChild(ga);
    	  })();
    	</script>
	
</body>
</html>
