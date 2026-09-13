workspace "The Librarian Pattern" "Separating probabilistic interpretation from authoritative state change." {

    model {
        source = softwareSystem "Source" "Raw or untrusted information such as interactions, documents, research findings, or external data."

        librarian = softwareSystem "LLM Librarian" "Uses probabilistic interpretation to extract, classify, normalize, compress, and propose structured information." {
            tags "Probabilistic"
        }

        governedState = softwareSystem "Governed Knowledge Lifecycle" "Owns validation, provenance, lifecycle transitions, authority decisions, and canonical state." {
            tags "Governed"

            validator = container "Proposal Validator" "Deterministically validates schema, types, domains, classifications, and constraints." "Deterministic Policy" {
                tags "Governed,Policy"
            }

            candidateFactory = container "Candidate Factory" "Creates governed candidates and attaches system-owned identity and provenance." "Deterministic Service" {
                tags "Governed,Service"
            }

            candidateStore = container "Candidate Store" "Persists validated candidates without granting canonical authority." "Authoritative Store" {
                tags "Governed,AuthoritativeStore"
            }

            promotionPolicy = container "Promotion Policy" "Determines whether a candidate may become a canonical artifact." "Deterministic Policy" {
                tags "Governed,Policy"
            }

            canonicalStore = container "Canonical Store" "Stores canonical artifacts and owns their authoritative lifecycle and activation state." "Authoritative Store" {
                tags "Governed,AuthoritativeStore"
            }

            activationPolicy = container "Activation Policy" "Applies domain-specific authority rules that determine whether a canonical artifact may become active, such as explicit consent or trusted provenance." "Deterministic Policy" {
                tags "Governed,Policy"
            }

            retrievalPolicy = container "Retrieval Eligibility Policy" "Derives retrieval eligibility exclusively from canonical lifecycle state." "Deterministic Policy" {
                tags "Governed,Policy"
            }
        }

        derivedIndex = softwareSystem "Derived Index" "Reflects retrieval-eligible canonical state for semantic or other derived retrieval mechanisms." {
            tags "Derived"
        }

        domainAuthority = softwareSystem "Domain-Specific Authority" "Reference examples showing how activation and retrieval authority can differ by domain." {
            
            personalMemoryPolicy = container "Personal Memory Activation Policy" "Requires explicit user consent before canonical personal memory may become active." "Domain-Specific Policy" {
                tags "Governed,Policy"
            }

            knowledgePolicy = container "Knowledge Activation Policy" "Requires trusted provenance before canonical knowledge may become active." "Domain-Specific Policy" {
                tags "Governed,Policy"
            }

            domainRetrievalPolicy = container "Retrieval Eligibility" "Determines whether active canonical knowledge is eligible for retrieval." "Deterministic Policy" {
                tags "Governed,Policy"
            }
        }

        source -> librarian "Provides raw information"
        librarian -> validator "Proposes structured interpretation — no authority granted"

        validator -> candidateFactory "Passes admissible proposal"
        candidateFactory -> candidateStore "Persists candidate with system-owned identity and provenance"

        candidateStore -> promotionPolicy "Provides candidate for evaluation"
        promotionPolicy -> canonicalStore "Promotes approved candidate"

        canonicalStore -> activationPolicy "Submits canonical artifact for activation decision"
        activationPolicy -> canonicalStore "Updates canonical activation state"

        canonicalStore -> retrievalPolicy "Provides active canonical lifecycle state"
        retrievalPolicy -> derivedIndex "Synchronizes retrieval-eligible artifacts"

        canonicalStore -> personalMemoryPolicy "Personal Memory: requires explicit user consent"
        canonicalStore -> knowledgePolicy "Knowledge: requires trusted provenance"

        knowledgePolicy -> domainRetrievalPolicy "Active canonical knowledge"
        domainRetrievalPolicy -> derivedIndex "Synchronizes retrieval-eligible knowledge"
    }

    views {
        systemLandscape "LibrarianPatternOverview" {
            include *
            autoLayout lr
        }

        container governedState "GovernedLifecycle" {
            include *
            autoLayout lr
        }

        container domainAuthority "DomainSpecificAuthority" {
            include canonicalStore
            include personalMemoryPolicy
            include knowledgePolicy
            include domainRetrievalPolicy
            include derivedIndex
            autoLayout lr
        }

        styles {
            element "Probabilistic" {
                background #3B82F6
                color #FFFFFF
                stroke #2563EB
            }

            element "Governed" {
                background #F0FDF4
                color #14532D
                stroke #86B89A
            }

            element "Policy" {
                background #ECFDF5
                color #14532D
                stroke #86B89A
            }

            element "Service" {
                background #F0FDF4
                color #14532D
                stroke #86B89A
            }

            element "AuthoritativeStore" {
                background #D1FAE5
                color #064E3B
                stroke #47856D
                shape Cylinder
            }

            element "Derived" {
                background #E5E7EB
                color #374151
                stroke #9CA3AF
            }
        }
    }
}