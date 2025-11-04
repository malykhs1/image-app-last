import anvil.secrets
import anvil.media
from datetime import datetime
import json
import requests
import uuid
import logging

PRICE = 390.0

class ShopifyClient:
  """Client for interacting with the Shopify Admin API."""

  def __init__(self, shop_domain, admin_token, online_store_publication_id):
    """Initialize the Shopify client with configuration values."""
    self.shop_domain = shop_domain
    self.admin_token = admin_token
    self.online_store_publication_id = online_store_publication_id
    self.admin_api_url = f"https://{shop_domain}/admin/api/2025-01/graphql.json"
    self.headers = {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": admin_token
    }

  def _execute_graphql(self, query, variables=None):
    """Execute a GraphQL query against the Shopify Admin API."""
    if variables is None:
      variables = {}

    try:
      response = requests.post(
        self.admin_api_url,
        json={"query": query, "variables": variables},
        headers=self.headers
      )
      response.raise_for_status()
      return response.json()
    except requests.RequestException as e:
      error_body = getattr(e.response, 'text', '')
      logging.error(f"Shopify API error: {str(e)}")
      logging.error(f"Response body: {error_body}")
      raise ValueError(f"Shopify API error: {str(e)}")

  def upload_image(self, image_media):
    """Upload an image to Shopify and return the resource URL."""
    # Step 1: Request a staged upload
    filename = f"p_img_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
    image_bytes = image_media.get_bytes()

    staged_upload_mutation = """
        mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
          stagedUploadsCreate(input: $input) {
            stagedTargets {
              url
              parameters { name value }
              resourceUrl
            }
          }
        }
        """

    variables = {
      "input": [{
        "resource": "IMAGE",
        "filename": filename,
        "mimeType": "image/jpeg",
        "httpMethod": "POST",
      }]
    }

    upload_data = self._execute_graphql(staged_upload_mutation, variables)
    staged_target = upload_data["data"]["stagedUploadsCreate"]["stagedTargets"][0]
    upload_url = staged_target["url"]
    parameters = staged_target["parameters"]
    resource_url = staged_target["resourceUrl"]

    # Step 2: Upload the file to the URL with the provided parameters
    files = {"file": (filename, image_bytes, "image/jpeg")}
    form_data = {param["name"]: param["value"] for param in parameters}

    try:
      upload_result = requests.post(upload_url, files=files, data=form_data)
      upload_result.raise_for_status()
      return resource_url
    except requests.RequestException as e:
      logging.error(f"Failed to upload image to Shopify: {str(e)}")
      raise ValueError(f"Failed to upload image: {str(e)}")

  def create_product_with_variants(self, image_url, anvil_id, string_len_meters, title="Custom String Art", tags=None):
    """Create a Shopify product with variants and return product ID and variant ID."""
    if tags is None:
      tags = ['Custom']

    mutation = """
        mutation createProductAsynchronous($productSet: ProductSetInput!, $synchronous: Boolean!) {
          productSet(synchronous: $synchronous, input: $productSet) {
            product {
              id
              variants(first: 5) {
                nodes {
                  id
                  displayName
                }
              }
            }
            productSetOperation {
              id
              status
              userErrors { code field message }
            }
            userErrors { code field message }
          }
        }
        """

    variables = {
      "synchronous": True,
      "productSet": {
        "title": title,
        "descriptionHtml": f"Made from {string_len_meters} meters of string",
        "productType": "String Art",
        "vendor": "Custom String Art",
        "status": "ACTIVE",
        "tags": tags,
        "productOptions": [{
          "name": "Size",
          "position": 1,
          "values": [
            {"name": "40x40cm"},
          ]
        }],
        "files": [{
          "alt": "Product image",
          "contentType": "IMAGE",
          "originalSource": image_url,
        }],
        "metafields": [{
          "namespace": "seo",
          "key": "hidden",
          "type": "single_line_text_field",
          "value": "1",
        },
                       {
                         "namespace": "anvil",
                         "key": "id",
                         "type": "single_line_text_field",
                         "value": anvil_id
                       }],
        "variants": [
          {
            "optionValues": [{
              "optionName": "Size",
              "name": "40x40cm"
            }],
            "price": PRICE
          },
        ]
      }
    }

    print("Creating product with variables:", variables)
    result = self._execute_graphql(mutation, variables)
    print("Shopify response:", result)
    if 'errors' in result:
      user_errors = result['errors']
      error_messages = [error["message"] for error in user_errors]
      print(error_messages)
      raise ValueError(f"Product creation failed: {', '.join(error_messages)}")

      # Check for user errors
    user_errors = result["data"]["productSet"]["userErrors"]
    if user_errors:
      error_messages = [error["message"] for error in user_errors]
      print(error_messages)
      raise ValueError(f"Product creation failed: {', '.join(error_messages)}")

    product_id = result["data"]["productSet"]["product"]["id"]
    variants = result["data"]["productSet"]["product"]["variants"]["nodes"]
    print(variants)
    variant = variants[0]

    return product_id, variant["id"]

  def get_translatable_digests(self, resource_id, locale):
    query = """
        query($resourceId: ID!) {
          translatableResource(resourceId: $resourceId) {
            resourceId
            translatableContent {
              key
              digest
              locale
            }
          }
        }"""
    variables = {"resourceId": resource_id}

    data = self._execute_graphql(query, variables)

    print(data)
    if "errors" in data:
      raise Exception("Error fetching digests: " + json.dumps(data["errors"], indent=2))

    content = data["data"]["translatableResource"]["translatableContent"]
    return {item["key"]: item["digest"] for item in content}

  def register_translations(self, resource_id, string_len_meters):
    locale = 'he'
    digests = self.get_translatable_digests(resource_id, locale)
    query = """
        mutation translationsRegister($resourceId: ID!, $translations: [TranslationInput!]!) {
          translationsRegister(resourceId: $resourceId, translations: $translations) {
            translations {
              key
              locale
              value
            }
            userErrors {
              field
              message
            }
          }
        }
        """

    description_key = [key for key in digests if 'html' in key.lower()][0]
    print(description_key)

    variables = {
      "resourceId": resource_id,
      "translations": [
        {
          "locale": locale,
          "key": "title",
          "value": "יצירה מותאמת אישית",
          "translatableContentDigest": digests.get("title")
        },
        {
          "locale": locale,
          "key": description_key,
          "value": f"מחוט באורך {string_len_meters} מטרים",
          "translatableContentDigest": digests.get(description_key)
        }
      ]
    }

    result = self._execute_graphql(query, variables)
    print(result)

  def publish_product(self, product_id):
    """Publish a product to the online store sales channel."""
    mutation = """
        mutation PublishablePublish($productId: ID!, $publicationId: ID!) {
          publishablePublish(id: $productId, input: {publicationId: $publicationId}) {
            publishable {
              publishedOnPublication(publicationId: $publicationId)
            }
            userErrors { field message }
          }
        }
        """

    variables = {
      "productId": product_id,
      "publicationId": self.online_store_publication_id
    }

    result = self._execute_graphql(mutation, variables)

    if result.get("data", {}).get("publishablePublish", {}).get("userErrors"):
      errors = result["data"]["publishablePublish"]["userErrors"]
      error_messages = [error["message"] for error in errors]
      raise ValueError(f"Publishing failed: {', '.join(error_messages)}")

    return True

  def wait_for_product_image_ready(self, product_id):
    query = """
      query ProductMedia($productId: ID!){
        product(id: $productId) {
          title
          media(first: 1) {
            edges {
              node {
                ...fieldsForMediaTypes
              }
            }
          }
        }
      }
      
      fragment fieldsForMediaTypes on Media {
        status
      }
      """
    variables = {
      "productId": product_id,
    }

    i = 0
    while i < 10:
      i += 1
      result = self._execute_graphql(query, variables)
      if result['data']['product']['media']['edges'][0]['node']['status'] == 'READY':
        #print(f'image is ready at iter {i} !!!')
        break
        #delay maybe (via full python 3 on business plan)


  def get_publication_ids(self):
    """List all available sales channels (publications)."""
    query = """
        {
          publications(first: 10) {
            edges {
              node {
                id
                name
              }
            }
          }
        }
        """

    result = self._execute_graphql(query)
    publications = result["data"]["publications"]["edges"]
    return [(edge["node"]["id"], edge["node"]["name"]) for edge in publications]

def anvil_to_shopify(image_obj, anvil_id, locale, string_len_meters,
                     shop_domain="mc8hfv-ce.myshopify.com",
                     online_store_publication="gid://shopify/Publication/128141623411"):
  """Main function to create a Shopify product from an Anvil image."""
  admin_token = anvil.secrets.get_secret('admin_API_token')
  # Initialize the Shopify client
  client = ShopifyClient(shop_domain, admin_token, online_store_publication)

  # Upload the image
  image_url = client.upload_image(image_obj)

  # Create the product with variants
  product_id, variant_id = client.create_product_with_variants(image_url, anvil_id, string_len_meters)

  # Add hebrew translations
  client.register_translations(product_id, string_len_meters) 

  # Publish the product to the online store
  # Получаем правильный Publication ID для Online Store
  try:
    publications = client.get_publication_ids()
    print(f"Available publications: {publications}")
    online_store_pub = None
    for pub_id, pub_name in publications:
      if 'Online Store' in pub_name or 'online' in pub_name.lower():
        online_store_pub = pub_id
        break

    if online_store_pub:
      # Обновляем ID публикации и публикуем
      client.online_store_publication_id = online_store_pub
      client.publish_product(product_id)
      print(f"Published to: {online_store_pub}")
    else:
      print("Warning: Online Store publication not found")
  except Exception as e:
    print(f"Publishing warning: {e}")

  client.wait_for_product_image_ready(product_id)

  # Extract the variant number from the variant ID
  variant_number = variant_id.split('/')[-1]

  return variant_number

def add_variant_to_cart(variant_id, quantity=1, shop_domain="mc8hfv-ce.myshopify.com"):
  """
    Добавить товар в корзину Shopify через Storefront API
    Возвращает cart_id и checkout_url
    """
  storefront_token = anvil.secrets.get_secret('storefront_access_token')

  url = f"https://{shop_domain}/api/2024-10/graphql.json"
  headers = {
    "Content-Type": "application/json",
    "X-Shopify-Storefront-Access-Token": storefront_token
  }

  # Создаем корзину и добавляем товар
  mutation = """
    mutation cartCreate($input: CartInput!) {
      cartCreate(input: $input) {
        cart {
          id
          checkoutUrl
          lines(first: 10) {
            edges {
              node {
                id
                quantity
                merchandise {
                  ... on ProductVariant {
                    id
                    title
                    product {
                      title
                    }
                  }
                }
              }
            }
          }
        }
        userErrors {
          field
          message
        }
      }
    }
    """

  variables = {
    "input": {
      "lines": [
        {
          "merchandiseId": f"gid://shopify/ProductVariant/{variant_id}",
          "quantity": quantity
        }
      ]
    }
  }

  response = requests.post(url, json={"query": mutation, "variables": variables}, headers=headers)
  result = response.json()

  if "errors" in result or result.get("data", {}).get("cartCreate", {}).get("userErrors"):
    errors = result.get("errors") or result["data"]["cartCreate"]["userErrors"]
    error_messages = [error.get("message", str(error)) for error in errors]
    raise ValueError(f"Failed to add to cart: {', '.join(error_messages)}")

  cart = result["data"]["cartCreate"]["cart"]
  return {
    "cart_id": cart["id"],
    "checkout_url": cart["checkoutUrl"]
  }