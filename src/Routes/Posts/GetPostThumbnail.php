<?php
namespace Szurubooru\Routes\Posts;
use Szurubooru\Config;
use Szurubooru\Dao\PublicFileDao;
use Szurubooru\Entities\Post;
use Szurubooru\Routes\AbstractRoute;
use Szurubooru\Services\NetworkingService;
use Szurubooru\Services\PostService;
use Szurubooru\Services\PostThumbnailService;

class GetPostThumbnail extends AbstractRoute
{
	private $config;
	private $fileDao;
	private $postService;
	private $networkingService;
	private $postThumbnailService;

	public function __construct(
		Config $config,
		PublicFileDao $fileDao,
		PostService $postService,
		NetworkingService $networkingService,
		PostThumbnailService $postThumbnailService)
	{
		$this->config = $config;
		$this->fileDao = $fileDao;
		$this->postService = $postService;
		$this->networkingService = $networkingService;
		$this->postThumbnailService = $postThumbnailService;
	}

	public function getMethods()
	{
		return ['GET'];
	}

	public function getUrl()
	{
		return '/api/posts/:postName/thumbnail/:size';
	}

	public function work()
	{
		$size = $this->getArgument('size');
		$post = $this->postService->getByName($this->getArgument('postName'));
		$thumbnailName = $this->postThumbnailService->generateIfNeeded($post, $size, $size);
		$this->networkingService->serveFile($this->fileDao->getFullPath($thumbnailName));
	}
}
